import os
import traceback
import boto3
from botocore.exceptions import ClientError

from common.data_loader import get_assets
from common.ddb import decimal_to_float
from common.http import ok, err

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))


def handler(event, context):
    try:
        table_name = os.environ.get("TABLE_ASSETS")
        assets = []

        if table_name:
            try:
                table = dynamodb.Table(table_name)
                resp = table.scan()
                items = resp.get("Items", [])
                if items:
                    assets = [decimal_to_float(item) for item in items]
            except Exception:
                pass

        if not assets:
            assets = get_assets()

        return ok({"assets": assets})

    except Exception as e:
        traceback.print_exc()
        return err(500, "INTERNAL", f"Internal error: {str(e)}")
