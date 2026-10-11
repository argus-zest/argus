import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


REGIONAL_MODEL_ID = "amazon.nova-lite-v1:0"
logger = logging.getLogger(__name__)
DAILY_QUOTA_MESSAGE = (
    "AI analysis is temporarily unavailable because the daily processing limit has been reached. "
    "You can continue submitting your report manually."
)


class NovaError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def mock_mode_enabled() -> bool:
    """Enable conservative inference fixtures only for explicitly local execution.

    This does not mock S3, DynamoDB, Step Functions, or SES. Those dependencies
    must still be replaced by local test doubles; no cloud failure enables mocks.
    """
    flag = os.environ.get("USE_MOCKS", "false").lower()
    if flag not in ("true", "false"):
        raise NovaError("MOCK_CONFIGURATION", "USE_MOCKS must be true or false")
    if flag != "true":
        return False
    local_sam = os.environ.get("AWS_SAM_LOCAL", "false").lower() == "true"
    deployed = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME")) or os.environ.get(
        "AWS_EXECUTION_ENV", ""
    ).startswith("AWS_Lambda_")
    if os.environ.get("ARGUS_ENV") != "local" or (deployed and not local_sam):
        raise NovaError("MOCK_CONFIGURATION", "Mock inference requires explicit local execution")
    return True


def get_bedrock_client():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    if region != "ap-southeast-2":
        raise NovaError("REGION_POLICY", "Bedrock inference must remain in ap-southeast-2")
    # Classify the service response before deciding whether a retry is safe.
    # Bedrock's daily token cap also arrives as ThrottlingException, but is not transient.
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(retries={"total_max_attempts": 1, "mode": "standard"}),
    )


def converse(
    messages: List[Dict[str, Any]],
    system: str | List[Dict[str, Any]],
    tool_config: Optional[Dict[str, Any]] = None,
    max_tokens: int = 800,
    temperature: float = 0.1,
) -> Dict[str, Any]:
    primary_model = os.environ.get("NOVA_MODEL_ID", REGIONAL_MODEL_ID)
    if primary_model != REGIONAL_MODEL_ID:
        raise NovaError(
            "REGION_POLICY",
            f"NOVA_MODEL_ID must be {REGIONAL_MODEL_ID} for in-Region inference in ap-southeast-2",
        )

    if mock_mode_enabled():
        raise NovaError("LOCAL_MOCK_UNSUPPORTED", "Local mocks are available only through the typed analysis helpers")
    client = get_bedrock_client()
    system_param = [{"text": system}] if isinstance(system, str) else system

    kwargs: Dict[str, Any] = {
        "modelId": REGIONAL_MODEL_ID,
        "messages": messages,
        "system": system_param,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }
    if tool_config:
        kwargs["toolConfig"] = tool_config

    for attempt in range(2):
        try:
            return client.converse(**kwargs)
        except ClientError as e:
            error = e.response.get("Error", {})
            err_code = str(error.get("Code", "MODEL_ERROR"))
            err_message = str(error.get("Message", ""))
            request_id = e.response.get("ResponseMetadata", {}).get("RequestId", "unknown")
            if err_code == "ThrottlingException":
                if "token" in err_message.lower() and any(
                    marker in err_message.lower() for marker in ("per day", "daily", "tokens/day")
                ):
                    logger.warning("Bedrock daily token quota exhausted request_id=%s", request_id)
                    raise NovaError("DAILY_QUOTA_EXHAUSTED", DAILY_QUOTA_MESSAGE) from None
                if attempt == 0:
                    logger.info("Bedrock transient throttle; retrying once request_id=%s", request_id)
                    time.sleep(0.25)
                    continue
                logger.warning("Bedrock transient throttling persisted request_id=%s", request_id)
                raise NovaError(
                    "TRANSIENT_THROTTLING",
                    "AI analysis is temporarily busy. You can continue submitting your report manually.",
                ) from None
            logger.warning("Bedrock Converse failed code=%s request_id=%s", err_code, request_id)
            raise NovaError(err_code, "AI inference is temporarily unavailable.") from None
        except Exception as e:
            logger.warning("Bedrock Converse failed type=%s", type(e).__name__)
            raise NovaError("MODEL_ERROR", "AI inference is temporarily unavailable.") from None
    raise NovaError("TRANSIENT_THROTTLING", "AI inference is temporarily busy.")


def _extract_tool_or_json(response: Dict[str, Any], tool_name: str) -> Optional[Dict[str, Any]]:
    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])

    for block in content:
        if "toolUse" in block and block["toolUse"].get("name") == tool_name:
            inp = block["toolUse"].get("input")
            if isinstance(inp, dict):
                return inp

    # Fallback to parsing JSON from text
    for block in content:
        if "text" in block:
            match = re.search(r"\{.*\}", block["text"], re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
    return None


def analyze_hazard(image_bytes: bytes, fmt: str) -> Dict[str, Any]:
    fmt_clean = fmt.lower()
    if fmt_clean == "jpg":
        fmt_clean = "jpeg"

    if fmt_clean not in ["jpeg", "png"]:
        raise NovaError("BAD_REQUEST", f"Unsupported image format: {fmt}. Must be jpeg or png.")

    if len(image_bytes) > 3.5 * 1024 * 1024:
        raise NovaError("IMAGE_TOO_LARGE", "Image exceeds maximum allowed size of 3.5 MB")

    if mock_mode_enabled():
        return {
            "hazard_type": "unclear", "severity": 0, "submerged": False,
            "confidence": 0.0, "description": "Local mock: no image inference performed",
            "visible_evidence": "Local mock fixture; image not inspected",
            "mock": True, "source": "local_mock",
        }

    tool_config = {
        "tools": [
            {
                "toolSpec": {
                    "name": "report_hazard",
                    "description": "Report the road hazard assessment",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "hazard_type": {
                                    "type": "string",
                                    "enum": [
                                        "pothole",
                                        "open_manhole",
                                        "missing_drain_cover",
                                        "waterlogging",
                                        "none",
                                        "unclear",
                                    ],
                                },
                                "severity": {"type": "integer", "minimum": 0, "maximum": 5},
                                "submerged": {"type": "boolean"},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "description": {"type": "string", "maxLength": 200},
                                "visible_evidence": {"type": "string", "maxLength": 200},
                            },
                            "required": [
                                "hazard_type",
                                "severity",
                                "submerged",
                                "confidence",
                                "description",
                                "visible_evidence",
                            ],
                        }
                    },
                }
            }
        ],
        "toolChoice": {"tool": {"name": "report_hazard"}},
    }

    system_prompt = (
        "You are a road-safety inspector for Delhi. Look ONLY at the image. Report the single most "
        "dangerous hazard visible. If you cannot see a clear hazard, use hazard_type 'none' or 'unclear'. "
        "Never guess hidden objects: if water covers the road and you cannot see a hole, say so and set "
        "submerged true. Be conservative with confidence."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": fmt_clean,
                        "source": {"bytes": image_bytes},
                    }
                },
                {"text": "Analyze the road hazard in this image."},
            ],
        }
    ]

    try:
        resp = converse(messages=messages, system=system_prompt, tool_config=tool_config)
        parsed = _extract_tool_or_json(resp, "report_hazard")
        if not _valid_hazard_response(parsed):
            logger.warning("Bedrock returned incomplete hazard assessment")
            raise NovaError("MALFORMED_MODEL_RESPONSE", "AI analysis returned an incomplete assessment.")
        h_type = parsed["hazard_type"]
        severity = 0 if h_type == "none" else parsed["severity"]
        return {
            "hazard_type": h_type,
            "severity": severity,
            "submerged": parsed["submerged"],
            "confidence": round(parsed["confidence"], 4),
            "description": parsed["description"][:200],
            "visible_evidence": parsed["visible_evidence"][:200],
            "source": "bedrock",
        }
    except NovaError:
        raise
    except Exception:
        pass

    raise NovaError("MALFORMED_MODEL_RESPONSE", "AI analysis returned an incomplete assessment.")


def _valid_hazard_response(parsed: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(parsed, dict):
        return False
    return (
        parsed.get("hazard_type") in {"pothole", "open_manhole", "missing_drain_cover", "waterlogging", "none", "unclear"}
        and isinstance(parsed.get("severity"), int)
        and not isinstance(parsed.get("severity"), bool)
        and 0 <= parsed["severity"] <= 5
        and isinstance(parsed.get("submerged"), bool)
        and isinstance(parsed.get("confidence"), (int, float))
        and not isinstance(parsed.get("confidence"), bool)
        and 0 <= parsed["confidence"] <= 1
        and isinstance(parsed.get("description"), str)
        and isinstance(parsed.get("visible_evidence"), str)
    )


def verify_fix(
    before_bytes: Optional[bytes],
    after_bytes: bytes,
    hazard_type: str,
    before_format: str = "jpeg",
    after_format: str = "jpeg",
) -> Dict[str, Any]:
    if len(after_bytes) > 3.5 * 1024 * 1024:
        raise NovaError("IMAGE_TOO_LARGE", "Repaired image exceeds maximum allowed size of 3.5 MB")
    if before_bytes is not None and len(before_bytes) > 3.5 * 1024 * 1024:
        raise NovaError("IMAGE_TOO_LARGE", "Original image exceeds maximum allowed size of 3.5 MB")

    if mock_mode_enabled():
        return {
            "hazard_still_present": True, "same_location_plausible": None,
            "confidence": 0.0, "explanation": "Local mock: repair was not verified",
            "mock": True, "source": "local_mock",
        }

    tool_config = {
        "tools": [
            {
                "toolSpec": {
                    "name": "report_verification",
                    "description": "Report verification of repaired road hazard",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "hazard_still_present": {"type": "boolean"},
                                "same_location_plausible": {"type": "boolean"},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "explanation": {"type": "string", "maxLength": 200},
                            },
                            "required": [
                                "hazard_still_present",
                                "confidence",
                                "explanation",
                            ],
                        }
                    },
                }
            }
        ],
        "toolChoice": {"tool": {"name": "report_verification"}},
    }

    system_prompt = (
        f"You are a road verification auditor inspecting whether a previously reported {hazard_type} "
        "has been repaired. Determine if the hazard is still present and if the repaired photo shows the same location."
    )

    user_content: List[Dict[str, Any]] = []
    if before_bytes:
        user_content.extend([
            {"text": "Before repair image:"},
            {"image": {"format": before_format.lower().replace("jpg", "jpeg"), "source": {"bytes": before_bytes}}},
        ])
    else:
        user_content.append({"text": "No before photo is available for comparison."})

    user_content.extend([
        {"text": "After repair image:"},
        {"image": {"format": after_format.lower().replace("jpg", "jpeg"), "source": {"bytes": after_bytes}}},
        {"text": "Verify if the hazard is resolved."},
    ])

    messages = [{"role": "user", "content": user_content}]

    try:
        resp = converse(messages=messages, system=system_prompt, tool_config=tool_config)
        parsed = _extract_tool_or_json(resp, "report_verification")
        if not _valid_verification_response(parsed, before_bytes is not None):
            logger.warning("Bedrock returned incomplete repair verification")
            raise NovaError("MALFORMED_MODEL_RESPONSE", "AI repair verification returned an incomplete result.")
        return {
            "hazard_still_present": parsed["hazard_still_present"],
            "same_location_plausible": parsed.get("same_location_plausible") if before_bytes else None,
            "confidence": round(parsed["confidence"], 4),
            "explanation": parsed["explanation"][:200],
            "source": "bedrock",
        }
    except NovaError:
        raise
    except Exception:
        pass

    raise NovaError("MALFORMED_MODEL_RESPONSE", "AI repair verification returned an incomplete result.")


def _valid_verification_response(parsed: Optional[Dict[str, Any]], compare_location: bool) -> bool:
    if not isinstance(parsed, dict):
        return False
    same_location = parsed.get("same_location_plausible")
    return (
        isinstance(parsed.get("hazard_still_present"), bool)
        and isinstance(parsed.get("confidence"), (int, float))
        and not isinstance(parsed.get("confidence"), bool)
        and 0 <= parsed["confidence"] <= 1
        and isinstance(parsed.get("explanation"), str)
        and (not compare_location or isinstance(same_location, bool))
    )


def extract_clause(pdf_bytes: bytes, doc_name: str) -> Dict[str, Any]:
    if mock_mode_enabled():
        return {
            "found": False, "quote": "", "page_hint": "",
            "verified_in_text": False, "mock": True, "source": "local_mock",
        }

    sanitized_name = re.sub(r"[^a-zA-Z0-9\s-]", "", doc_name).strip()[:100]
    if not sanitized_name:
        sanitized_name = "tender-doc"

    tool_config = {
        "tools": [
            {
                "toolSpec": {
                    "name": "report_clause",
                    "description": "Report maintenance and defect liability clause from tender PDF",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "found": {"type": "boolean"},
                                "quote": {"type": "string", "maxLength": 600},
                                "page_hint": {"type": "string"},
                            },
                            "required": ["found", "quote", "page_hint"],
                        }
                    },
                }
            }
        ],
        "toolChoice": {"tool": {"name": "report_clause"}},
    }

    system_prompt = (
        "Find the clause about maintenance, defect liability, or warranty of bituminous or road work. "
        "Copy it VERBATIM. If none exists, found=false. Do not paraphrase."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "document": {
                        "format": "pdf",
                        "name": sanitized_name,
                        "source": {"bytes": pdf_bytes},
                    }
                },
                {"text": "Extract the defect liability or maintenance warranty clause from this tender document."},
            ],
        }
    ]

    try:
        resp = converse(messages=messages, system=system_prompt, tool_config=tool_config)
        parsed = _extract_tool_or_json(resp, "report_clause")
        if parsed:
            found = bool(parsed.get("found", False))
            quote = str(parsed.get("quote", ""))[:600]
            page_hint = str(parsed.get("page_hint", ""))
            return {
                "found": found,
                "quote": quote if found else "",
                "page_hint": page_hint,
                "verified_in_text": True if found else False,
            }
    except NovaError:
        raise
    except Exception:
        pass

    return {
        "found": False,
        "quote": "",
        "page_hint": "",
        "verified_in_text": False,
    }
