import json
import os
import uuid
import boto3
from botocore.config import Config
from common.http import ok, err, parse_json


def get_s3_client():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client(
        "s3", region_name=region,
        endpoint_url=f"https://s3.{region}.amazonaws.com",
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )


def lambda_handler(event, context):
    try:
        body = parse_json(event)
    except Exception as e:
        return err(400, "BAD_REQUEST", f"Invalid JSON body: {str(e)}")

    purpose = body.get("purpose")
    content_type = body.get("content_type")

    if purpose not in ["report", "fix"]:
        return err(400, "BAD_REQUEST", "purpose must be 'report' or 'fix'")

    if content_type not in ["image/jpeg", "image/png"]:
        return err(400, "BAD_REQUEST", "content_type must be 'image/jpeg' or 'image/png'")

    bucket = os.environ.get("BUCKET", "argus-uploads")
    ext = ".jpg" if content_type == "image/jpeg" else ".png"
    s3_key = f"uploads/{uuid.uuid4()}{ext}"

    try:
        s3 = get_s3_client()
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=300,
        )

        return ok({
            "upload_url": upload_url,
            "s3_key": s3_key,
            "expires_in": 300,
        })
    except Exception as e:
        return err(500, "INTERNAL", f"Could not generate presigned URL: {str(e)}")
