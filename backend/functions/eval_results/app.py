import json
import os
import traceback
import boto3
from botocore.exceptions import ClientError
from common.http import ok, err

s3_client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def _read_s3_json(bucket: str, key: str):
    try:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        return json.loads(resp["Body"].read().decode("utf-8"))
    except (ClientError, Exception):
        return None


def handler(event, context):
    try:
        bucket = os.environ.get("BUCKET")
        rdd2022_data = None
        backtest_data = None

        if bucket:
            rdd2022_data = _read_s3_json(bucket, "eval/rdd2022.json")
            backtest_data = _read_s3_json(bucket, "eval/backtest.json")

        return ok({
            "rdd2022": rdd2022_data,
            "backtest": backtest_data,
        })
    except Exception as e:
        traceback.print_exc()
        return err(500, "INTERNAL", f"Internal error: {str(e)}")
