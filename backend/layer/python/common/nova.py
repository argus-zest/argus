import json
import os
import re
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError


REGIONAL_MODEL_ID = "amazon.nova-lite-v1:0"


class NovaError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def get_bedrock_client():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client("bedrock-runtime", region_name=region)


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

    try:
        return client.converse(**kwargs)
    except ClientError as e:
        err_code = e.response.get("Error", {}).get("Code", "")
        raise NovaError(err_code or "MODEL_ERROR", str(e))
    except Exception as e:
        raise NovaError("MODEL_ERROR", str(e))


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
        if parsed:
            # Clamp and validate fields
            h_type = str(parsed.get("hazard_type", "unclear"))
            if h_type not in ["pothole", "open_manhole", "missing_drain_cover", "waterlogging", "none", "unclear"]:
                h_type = "unclear"
            sev = int(parsed.get("severity", 0))
            if h_type == "none":
                sev = 0
            sev = max(0, min(5, sev))
            sub = bool(parsed.get("submerged", False))
            conf = float(parsed.get("confidence", 0.0))
            conf = max(0.0, min(1.0, conf))
            desc = str(parsed.get("description", ""))[:200]
            vis = str(parsed.get("visible_evidence", ""))[:200]

            return {
                "hazard_type": h_type,
                "severity": sev,
                "submerged": sub,
                "confidence": round(conf, 4),
                "description": desc,
                "visible_evidence": vis,
            }
    except NovaError:
        raise
    except Exception:
        pass

    return {
        "hazard_type": "unclear",
        "severity": 0,
        "submerged": False,
        "confidence": 0.0,
        "description": "Could not identify hazard",
        "visible_evidence": "Unclear image",
    }


def verify_fix(
    before_bytes: Optional[bytes],
    after_bytes: bytes,
    hazard_type: str,
) -> Dict[str, Any]:
    if len(after_bytes) > 3.5 * 1024 * 1024:
        raise NovaError("IMAGE_TOO_LARGE", "Repaired image exceeds maximum allowed size of 3.5 MB")

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
            {"image": {"format": "jpeg", "source": {"bytes": before_bytes}}},
        ])
    else:
        user_content.append({"text": "No before photo is available for comparison."})

    user_content.extend([
        {"text": "After repair image:"},
        {"image": {"format": "jpeg", "source": {"bytes": after_bytes}}},
        {"text": "Verify if the hazard is resolved."},
    ])

    messages = [{"role": "user", "content": user_content}]

    try:
        resp = converse(messages=messages, system=system_prompt, tool_config=tool_config)
        parsed = _extract_tool_or_json(resp, "report_verification")
        if parsed:
            still_present = bool(parsed.get("hazard_still_present", True))
            same_loc = parsed.get("same_location_plausible")
            if before_bytes is None:
                same_loc = None
            elif same_loc is not None:
                same_loc = bool(same_loc)

            conf = float(parsed.get("confidence", 0.0))
            expl = str(parsed.get("explanation", ""))[:200]
            return {
                "hazard_still_present": still_present,
                "same_location_plausible": same_loc,
                "confidence": round(max(0.0, min(1.0, conf)), 4),
                "explanation": expl,
            }
    except NovaError:
        raise
    except Exception:
        pass

    return {
        "hazard_still_present": True,
        "same_location_plausible": None if before_bytes is None else False,
        "confidence": 0.0,
        "explanation": "Could not verify repair photo.",
    }


def extract_clause(pdf_bytes: bytes, doc_name: str) -> Dict[str, Any]:
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
