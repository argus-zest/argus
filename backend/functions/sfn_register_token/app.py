import os
from datetime import datetime, timezone
import boto3
from common.ddb import float_to_decimal


def get_dynamodb():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.resource("dynamodb", region_name=region)


def lambda_handler(event, context):
    case_id = event.get("case_id")
    rung = int(event.get("rung", 1))
    token = event.get("token")

    if not case_id or not token:
        raise ValueError("case_id and token are required")

    status = "ESCALATED_DM" if rung == 4 else "AWAITING_FIX"
    now_iso = datetime.now(timezone.utc).isoformat()

    ddb = get_dynamodb()
    cases_table = ddb.Table(os.environ.get("TABLE_CASES", "argus-Cases"))

    cases_table.update_item(
        Key={"case_id": case_id},
        UpdateExpression="SET current_task_token = :tok, #st = :st, rung = :r, updated_at = :now",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":tok": token,
            ":st": status,
            ":r": rung,
            ":now": now_iso,
        },
    )

    return {"status": "REGISTERED", "case_id": case_id, "rung": rung}
