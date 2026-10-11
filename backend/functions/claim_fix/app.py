import json
import os
from datetime import datetime, timezone
import boto3
from common.http import ok, err, parse_json
from common.geo import haversine
from common.nova import verify_fix
from common.ddb import float_to_decimal, decimal_to_float


def get_dynamodb():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.resource("dynamodb", region_name=region)


def get_s3():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client("s3", region_name=region)


def get_sfn():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client("stepfunctions", region_name=region)


def append_event(table_events, case_id: str, ev_type: str, message: str, rung: int, meta: dict):
    now_iso = datetime.now(timezone.utc).isoformat()
    ts_seq = f"{now_iso}#{int(datetime.now(timezone.utc).timestamp() * 1000) % 10000:04d}"
    item = {
        "case_id": case_id,
        "ts_seq": ts_seq,
        "type": ev_type,
        "message": message,
        "rung": rung,
        "meta": meta or {},
    }
    table_events.put_item(Item=float_to_decimal(item))


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        case_id = path_params.get("case_id")
        if not case_id:
            raw_path = event.get("rawPath") or event.get("requestContext", {}).get("http", {}).get("path", "")
            parts = [p for p in raw_path.split("/") if p]
            if "cases" in parts:
                idx = parts.index("cases")
                if len(parts) > idx + 1:
                    case_id = parts[idx + 1]

        if not case_id:
            return err(400, "BAD_REQUEST", "case_id is required")

        body = parse_json(event)
        s3_key = body.get("s3_key")
        lat = body.get("lat")
        lng = body.get("lng")

        if not s3_key or lat is None or lng is None:
            return err(400, "BAD_REQUEST", "s3_key, lat, and lng are required")

        ddb = get_dynamodb()
        cases_table = ddb.Table(os.environ.get("TABLE_CASES", "argus-Cases"))
        events_table = ddb.Table(os.environ.get("TABLE_EVENTS", "argus-CaseEvents"))

        case_resp = cases_table.get_item(Key={"case_id": case_id})
        if "Item" not in case_resp:
            return err(404, "NOT_FOUND", f"Case {case_id} not found")

        case_data = decimal_to_float(case_resp["Item"])
        status = case_data.get("status")
        rung = case_data.get("rung", 1)

        # Step 1: Check status
        if status not in ["AWAITING_FIX", "OPEN", "ESCALATED_DM"]:
            return ok({
                "accepted": False,
                "reason": "CASE_NOT_OPEN",
                "distance_m": 0.0,
                "verification": None,
            })

        # Step 2: Distance gate
        case_lat = case_data.get("lat")
        case_lng = case_data.get("lng")
        distance_m = haversine(float(lat), float(lng), float(case_lat), float(case_lng))

        if distance_m > 25.0:
            append_event(
                events_table,
                case_id,
                "CLOSURE_REJECTED",
                f"Claimed fix rejected: distance {distance_m:.1f} m exceeds 25 m gate",
                rung,
                {"reason": "TOO_FAR", "distance_m": distance_m},
            )
            return ok({
                "accepted": False,
                "reason": "TOO_FAR",
                "distance_m": round(distance_m, 2),
                "verification": None,
            })

        # Step 3: Fetch images
        s3 = get_s3()
        bucket = os.environ.get("BUCKET", "argus-uploads")

        before_bytes = None
        before_key = case_data.get("photo_key")
        if before_key:
            try:
                resp = s3.get_object(Bucket=bucket, Key=before_key)
                before_bytes = resp["Body"].read()
            except Exception:
                before_bytes = None

        after_resp = s3.get_object(Bucket=bucket, Key=s3_key)
        after_bytes = after_resp["Body"].read()

        analysis = case_data.get("analysis") or {}
        hazard_type = analysis.get("hazard_type", "pothole")

        verification = verify_fix(before_bytes, after_bytes, hazard_type)

        # Step 4: Verification criteria
        hazard_still_present = verification.get("hazard_still_present", True)
        same_loc = verification.get("same_location_plausible")
        confidence = verification.get("confidence", 0.0)

        loc_ok = (same_loc is True or same_loc is None)
        accepted = (not hazard_still_present) and loc_ok and (confidence >= 0.6)

        task_token = case_data.get("current_task_token")
        sfn = get_sfn() if task_token else None

        if accepted:
            # Step 5a: Accept
            append_event(
                events_table,
                case_id,
                "FIX_CLAIMED",
                "Claimant submitted fix verification photo",
                rung,
                {"s3_key": s3_key, "distance_m": distance_m},
            )
            append_event(
                events_table,
                case_id,
                "CLOSURE_VERIFIED",
                f"Closure verified by Nova: {verification.get('explanation')}",
                rung,
                {"verification": verification},
            )
            cases_table.update_item(
                Key={"case_id": case_id},
                UpdateExpression="SET #st = :st, updated_at = :now",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":st": "CLOSED_VERIFIED",
                    ":now": datetime.now(timezone.utc).isoformat(),
                },
            )
            if sfn and task_token:
                try:
                    sfn.send_task_success(
                        taskToken=task_token,
                        output=json.dumps({"verified": True}),
                    )
                except Exception as sfn_err:
                    print(f"send_task_success warning: {sfn_err}")

            return ok({
                "accepted": True,
                "reason": "VERIFIED",
                "distance_m": round(distance_m, 2),
                "verification": verification,
            })
        else:
            # Step 5b: Reject
            if hazard_still_present:
                reason = "HAZARD_STILL_PRESENT"
            elif same_loc is False:
                reason = "LOCATION_MISMATCH"
            else:
                reason = "LOW_CONFIDENCE"

            append_event(
                events_table,
                case_id,
                "CLOSURE_REJECTED",
                f"Closure rejected ({reason}): {verification.get('explanation')}",
                rung,
                {"reason": reason, "verification": verification},
            )

            if sfn and task_token:
                try:
                    sfn.send_task_failure(
                        taskToken=task_token,
                        error="ClosureRejected",
                        cause=reason,
                    )
                except Exception as sfn_err:
                    print(f"send_task_failure warning: {sfn_err}")

            return ok({
                "accepted": False,
                "reason": reason,
                "distance_m": round(distance_m, 2),
                "verification": verification,
            })
    except Exception as e:
        return err(500, "INTERNAL", f"Claim fix error: {str(e)}")
