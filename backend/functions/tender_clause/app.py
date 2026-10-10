import os
import boto3
from botocore.exceptions import ClientError
from common.http import ok, err, parse_json
from common.nova import extract_clause, NovaError


def get_s3_client():
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.client("s3", region_name=region)


def lambda_handler(event, context):
    try:
        body = parse_json(event)
    except Exception as e:
        return err(400, "BAD_REQUEST", f"Invalid JSON body: {str(e)}")

    doc_key = body.get("doc_key")
    if not doc_key or not isinstance(doc_key, str):
        return err(400, "BAD_REQUEST", "doc_key is required")

    if not doc_key.startswith("tenders/"):
        return err(400, "BAD_REQUEST", "doc_key must start with 'tenders/'")

    bucket = os.environ.get("BUCKET", "argus-uploads")

    try:
        s3 = get_s3_client()
        resp = s3.get_object(Bucket=bucket, Key=doc_key)
        pdf_bytes = resp["Body"].read()
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "NoSuchKey":
            return err(404, "NOT_FOUND", f"Document not found at {doc_key}")
        return err(500, "INTERNAL", f"Failed to retrieve document: {str(e)}")
    except Exception as e:
        return err(500, "INTERNAL", f"Failed to retrieve document: {str(e)}")

    doc_name = os.path.basename(doc_key)

    try:
        result = extract_clause(pdf_bytes, doc_name)
        return ok(result)
    except NovaError as ne:
        return err(502, "MODEL_ERROR", ne.message)
    except Exception as e:
        return err(500, "INTERNAL", f"Unexpected error during clause extraction: {str(e)}")
