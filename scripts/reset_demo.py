import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
import boto3

# Ensure layer is importable
sys.path.insert(0, os.path.abspath("backend/layer/python"))
from common.ddb import decimal_to_float
import scripts.seed_demo as seed_demo


def get_dynamodb(profile: str, region: str):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.resource("dynamodb")


def main():
    parser = argparse.ArgumentParser(description="Reset demo data: delete seeded & demo_run cases, then re-seed")
    parser.add_argument("--profile", default="hackathon", help="AWS profile name")
    parser.add_argument("--region", default="ap-southeast-2", help="AWS region")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting")
    args = parser.parse_args()

    table_cases_name = os.environ.get("TABLE_CASES", "argus-Cases")
    table_events_name = os.environ.get("TABLE_EVENTS", "argus-CaseEvents")
    table_assets_name = os.environ.get("TABLE_ASSETS", "argus-Assets")

    print(f"[*] Resetting demo cases (profile={args.profile}, region={args.region}, dry_run={args.dry_run})...")

    if args.dry_run:
        print(f"Would scan {table_cases_name} and delete items where seeded=true or (demo_run=true and created within 24h)")
        print(f"Would delete associated {table_events_name} and seeded {table_assets_name}")
        print("Would invoke seed_demo.py to recreate canonical demo dataset.")
        return

    ddb = get_dynamodb(args.profile, args.region)
    table_cases = ddb.Table(table_cases_name)
    table_events = ddb.Table(table_events_name)
    table_assets = ddb.Table(table_assets_name)

    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=24)).isoformat()

    # 1. Scan and delete matching cases
    resp = table_cases.scan()
    items = resp.get("Items", [])
    cases_to_delete = []

    for it in items:
        data = decimal_to_float(it)
        is_seeded = data.get("seeded", False)
        is_demo = data.get("demo_run", False)
        created_at = data.get("created_at", "")

        if is_seeded or (is_demo and created_at >= cutoff):
            cases_to_delete.append(data["case_id"])

    print(f"[*] Found {len(cases_to_delete)} cases to delete.")

    for cid in cases_to_delete:
        # Delete case
        table_cases.delete_item(Key={"case_id": cid})

        # Query and delete events for this case
        ev_resp = table_events.query(
            KeyConditionExpression="case_id = :cid",
            ExpressionAttributeValues={":cid": cid},
        )
        for ev in ev_resp.get("Items", []):
            table_events.delete_item(Key={"case_id": cid, "ts_seq": ev["ts_seq"]})

    # 2. Delete seeded assets
    asset_resp = table_assets.scan()
    for ast in asset_resp.get("Items", []):
        if ast.get("seeded"):
            table_assets.delete_item(Key={"asset_id": ast["asset_id"]})

    print("[+] Deletions complete. Re-seeding canonical demo data...")

    # 3. Call seed_demo
    sys.argv = ["seed_demo.py", "--profile", args.profile, "--region", args.region]
    seed_demo.main()
    print("[+] Reset and re-seed successfully finished.")


if __name__ == "__main__":
    main()
