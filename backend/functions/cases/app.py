import json
import os
import random
import string
from datetime import datetime, timezone
import boto3
from common.http import ok, err, parse_json
from common.geo import road_for_point
from common.jurisdiction import resolve_jurisdiction
from common.warranty import compute_warranty
from common.data_loader import load_roads, load_hotspots, load_contracts
from common.ddb import float_to_decimal, decimal_to_float


def get_dynamodb():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.resource("dynamodb", region_name=region)


def get_sfn():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client("stepfunctions", region_name=region)


def get_s3():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client("s3", region_name=region)


def generate_case_id() -> str:
    chars = string.ascii_uppercase + string.digits
    rand_part = "".join(random.choices(chars, k=6))
    return f"CS-{rand_part}"


def append_event(table_events, case_id: str, ev_type: str, message: str, rung: int, meta: dict, seq_num: int = 1):
    now_iso = datetime.now(timezone.utc).isoformat()
    ts_seq = f"{now_iso}#{seq_num:04d}"
    item = {
        "case_id": case_id,
        "ts_seq": ts_seq,
        "type": ev_type,
        "message": message,
        "rung": rung,
        "meta": meta or {},
    }
    table_events.put_item(Item=float_to_decimal(item))


def handle_create_case(event):
    try:
        body = parse_json(event)
    except Exception as e:
        return err(400, "BAD_REQUEST", f"Invalid JSON body: {str(e)}")

    hotspot_id = body.get("hotspot_id")
    lat = body.get("lat")
    lng = body.get("lng")

    if not hotspot_id and (lat is None or lng is None):
        return err(400, "BAD_REQUEST", "Either hotspot_id or lat and lng must be provided")

    hotspots = load_hotspots()
    roads = load_roads()
    contracts = load_contracts()

    target_road = None
    if hotspot_id:
        hs = next((h for h in hotspots if h["hotspot_id"] == hotspot_id), None)
        if hs:
            lat = hs["lat"]
            lng = hs["lng"]
            target_road = next((r for r in roads if r["road_id"] == hs.get("road_id")), None)

    if not target_road and lat is not None and lng is not None:
        target_road = road_for_point(roads, float(lat), float(lng))

    asset_type = body.get("asset_type")
    jurisdiction = resolve_jurisdiction(target_road, asset_type)

    today = datetime.now(timezone.utc).date()
    road_contracts = [c for c in contracts if target_road and c.get("road_id") == target_road.get("road_id")]
    selected_contract = None
    if road_contracts:
        selected_contract = sorted(road_contracts, key=lambda c: c.get("completion_date", ""), reverse=True)[0]
    warranty = compute_warranty(selected_contract, today)

    case_id = generate_case_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    start_rung = jurisdiction.get("start_rung", 1)

    timer_profile = body.get("timer_profile", "demo")
    if timer_profile not in ["demo", "real"]:
        timer_profile = "demo"

    timers = [20, 20, 20, 20] if timer_profile == "demo" else [259200, 172800, 172800, 259200]

    case_record = {
        "case_id": case_id,
        "hotspot_id": hotspot_id,
        "asset_id": body.get("asset_id"),
        "lat": float(lat),
        "lng": float(lng),
        "status": "OPEN",
        "rung": start_rung,
        "owner": jurisdiction.get("owner", "ORPHAN"),
        "jurisdiction": jurisdiction,
        "warranty": warranty,
        "analysis": body.get("analysis"),
        "photo_key": body.get("photo_key"),
        "execution_arn": None,
        "timer_profile": timer_profile,
        "dry_run": True,
        "seeded": False,
        "demo_run": True,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    ddb = get_dynamodb()
    cases_table = ddb.Table(os.environ.get("TABLE_CASES", "argus-Cases"))
    events_table = ddb.Table(os.environ.get("TABLE_EVENTS", "argus-CaseEvents"))

    # Write initial Case record
    cases_table.put_item(Item=float_to_decimal(case_record))

    # Append CASE_OPENED and JURISDICTION_RESOLVED
    append_event(events_table, case_id, "CASE_OPENED", "Case reported and registered", start_rung, {}, seq_num=1)
    append_event(
        events_table,
        case_id,
        "JURISDICTION_RESOLVED",
        f"Jurisdiction determined as {jurisdiction.get('owner')} ({jurisdiction.get('officer_role')})",
        start_rung,
        {"jurisdiction": jurisdiction},
        seq_num=2,
    )

    # Start Step Functions execution
    state_machine_arn = os.environ.get("STATE_MACHINE_ARN")
    if state_machine_arn:
        try:
            sfn = get_sfn()
            sfn_input = {
                "case_id": case_id,
                "rung": start_rung,
                "timers": timers,
            }
            exec_resp = sfn.start_execution(
                stateMachineArn=state_machine_arn,
                name=f"{case_id}-{int(datetime.now(timezone.utc).timestamp())}",
                input=json.dumps(sfn_input),
            )
            exec_arn = exec_resp.get("executionArn")
            case_record["execution_arn"] = exec_arn
            cases_table.update_item(
                Key={"case_id": case_id},
                UpdateExpression="SET execution_arn = :arn",
                ExpressionAttributeValues={":arn": exec_arn},
            )
        except Exception as sfn_err:
            append_event(
                events_table,
                case_id,
                "CASE_OPENED",
                f"Failed to start escalation execution: {str(sfn_err)}",
                start_rung,
                {"error": str(sfn_err)},
                seq_num=3,
            )
            return err(502, "INTERNAL", f"Could not initiate escalation workflow: {str(sfn_err)}")

    return ok(case_record, status=201)


def handle_get_case(case_id: str):
    ddb = get_dynamodb()
    cases_table = ddb.Table(os.environ.get("TABLE_CASES", "argus-Cases"))
    events_table = ddb.Table(os.environ.get("TABLE_EVENTS", "argus-CaseEvents"))

    case_resp = cases_table.get_item(Key={"case_id": case_id})
    if "Item" not in case_resp:
        return err(404, "NOT_FOUND", f"Case {case_id} not found")

    case_data = decimal_to_float(case_resp["Item"])
    if "current_task_token" in case_data:
        del case_data["current_task_token"]

    events_resp = events_table.query(
        KeyConditionExpression="case_id = :cid",
        ExpressionAttributeValues={":cid": case_id},
    )
    events_list = [decimal_to_float(item) for item in events_resp.get("Items", [])]
    events_list.sort(key=lambda x: x.get("ts_seq", ""))

    photo_url = None
    photo_key = case_data.get("photo_key")
    if photo_key:
        try:
            s3 = get_s3()
            bucket = os.environ.get("BUCKET", "argus-uploads")
            photo_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": photo_key},
                ExpiresIn=3600,
            )
        except Exception:
            pass

    return ok({
        "case": case_data,
        "events": events_list,
        "photo_url": photo_url,
    })


def handle_list_cases():
    ddb = get_dynamodb()
    cases_table = ddb.Table(os.environ.get("TABLE_CASES", "argus-Cases"))

    resp = cases_table.scan(Limit=50)
    items = [decimal_to_float(item) for item in resp.get("Items", [])]
    for item in items:
        if "current_task_token" in item:
            del item["current_task_token"]

    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return ok({"cases": items[:50]})


def handler(event, context):
    try:
        http_info = event.get("requestContext", {}).get("http", {})
        method = http_info.get("method", "GET")
        path = http_info.get("path", "/v1/cases")
        path_params = event.get("pathParameters") or {}

        if method == "POST" and (path == "/v1/cases" or path.endswith("/cases")):
            return handle_create_case(event)
        elif method == "GET":
            case_id = path_params.get("case_id")
            if case_id:
                return handle_get_case(case_id)
            elif "/cases/" in path:
                extracted_id = path.rstrip("/").split("/")[-1]
                if extracted_id and extracted_id != "cases":
                    return handle_get_case(extracted_id)
            return handle_list_cases()

        return err(404, "NOT_FOUND", "Endpoint not found")
    except Exception as e:
        return err(500, "INTERNAL", f"Server error: {str(e)}")
