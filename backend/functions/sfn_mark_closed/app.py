import os
from datetime import datetime, timezone
import boto3
from common.ddb import float_to_decimal


def get_dynamodb():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.resource("dynamodb", region_name=region)


def lambda_handler(event, context):
    case_id = event.get("case_id")
    outcome = event.get("outcome", "CLOSED_VERIFIED")

    if not case_id:
        raise ValueError("case_id is required")

    now_iso = datetime.now(timezone.utc).isoformat()
    ddb = get_dynamodb()
    cases_table = ddb.Table(os.environ.get("TABLE_CASES", "argus-Cases"))
    events_table = ddb.Table(os.environ.get("TABLE_EVENTS", "argus-CaseEvents"))

    if outcome == "UNRESOLVED_FINAL":
        status = "UNRESOLVED_FINAL"
        ts_seq = f"{now_iso}#{int(datetime.now(timezone.utc).timestamp() * 1000) % 10000:04d}"
        events_table.put_item(
            Item=float_to_decimal({
                "case_id": case_id,
                "ts_seq": ts_seq,
                "type": "UNRESOLVED_FINAL",
                "message": "Hazard remained unresolved through all 4 rungs of escalation",
                "rung": 4,
                "meta": {"outcome": "UNRESOLVED_FINAL"},
            })
        )
    else:
        status = "CLOSED_VERIFIED"

    cases_table.update_item(
        Key={"case_id": case_id},
        UpdateExpression="SET #st = :st, updated_at = :now REMOVE current_task_token",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":st": status,
            ":now": now_iso,
        },
    )

    return {"status": status, "case_id": case_id, "outcome": outcome}
