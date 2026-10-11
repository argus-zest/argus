import os
import logging
import boto3
from botocore.exceptions import ClientError
from common.http import ok, err, parse_json
from common.nova import analyze_hazard, NovaError

logger = logging.getLogger(__name__)


def get_s3_client():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client("s3", region_name=region)


def lambda_handler(event, context):
    try:
        body = parse_json(event)
    except Exception as e:
        return err(400, "BAD_REQUEST", f"Invalid JSON body: {str(e)}")

    s3_key = body.get("s3_key")
    if not s3_key or not isinstance(s3_key, str):
        return err(400, "BAD_REQUEST", "s3_key is required")

    bucket = os.environ.get("BUCKET", "argus-uploads")

    fmt = "png" if s3_key.lower().endswith(".png") else "jpeg"

    try:
        s3 = get_s3_client()
        resp = s3.get_object(Bucket=bucket, Key=s3_key)
        image_bytes = resp["Body"].read()
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "NoSuchKey":
            return err(404, "NOT_FOUND", f"Image not found at {s3_key}")
        return err(500, "INTERNAL", f"Failed to retrieve image: {str(e)}")
    except Exception as e:
        return err(500, "INTERNAL", f"Failed to retrieve image: {str(e)}")

    try:
        analysis = analyze_hazard(image_bytes, fmt)
        return ok({"analysis": analysis})
    except NovaError as ne:
        if ne.code == "IMAGE_TOO_LARGE":
            return err(413, "IMAGE_TOO_LARGE", ne.message)
        elif ne.code == "BAD_REQUEST":
            return err(400, "BAD_REQUEST", ne.message)
        elif ne.code == "DAILY_QUOTA_EXHAUSTED":
            return err(503, ne.code, ne.message)
        elif ne.code == "TRANSIENT_THROTTLING":
            return err(503, ne.code, ne.message)
        if ne.code == "MALFORMED_MODEL_RESPONSE":
            return err(502, ne.code, "AI analysis could not be interpreted. You can continue submitting your report manually.")
        logger.warning("Hazard analysis unavailable code=%s", ne.code)
        return err(503, "AI_ANALYSIS_UNAVAILABLE", "AI analysis is temporarily unavailable. You can continue submitting your report manually.")
    except Exception as e:
        return err(500, "INTERNAL", f"Unexpected error during analysis: {str(e)}")
