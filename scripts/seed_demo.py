import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
import boto3

# Ensure layer is importable
sys.path.insert(0, os.path.abspath("backend/layer/python"))
from common.data_loader import load_assets, load_hotspots
from common.ddb import float_to_decimal


def get_dynamodb(profile: str, region: str):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.resource("dynamodb")


def main():
    parser = argparse.ArgumentParser(description="Seed demo assets and cases into DynamoDB")
    parser.add_argument("--profile", default="hackathon", help="AWS profile name")
    parser.add_argument("--region", default="ap-southeast-2", help="AWS region")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying tables")
    args = parser.parse_args()

    assets = load_assets()
    hotspots = {h["hotspot_id"]: h for h in load_hotspots()}

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    table_assets_name = os.environ.get("TABLE_ASSETS", "argus-Assets")
    table_cases_name = os.environ.get("TABLE_CASES", "argus-Cases")
    table_events_name = os.environ.get("TABLE_EVENTS", "argus-CaseEvents")

    print(f"[*] Seeding demo data (profile={args.profile}, region={args.region}, dry_run={args.dry_run})...")

    if args.dry_run:
        print(f"Would seed {len(assets)} assets into {table_assets_name}")
        print(f"Would seed 3 demo cases into {table_cases_name} and {table_events_name}")
        return

    ddb = get_dynamodb(args.profile, args.region)
    table_assets = ddb.Table(table_assets_name)
    table_cases = ddb.Table(table_cases_name)
    table_events = ddb.Table(table_events_name)

    # 1. Seed Assets
    for a in assets:
        item = {
            "asset_id": a["asset_id"],
            "type": a["type"],
            "severity": a["severity"],
            "lat": a["lat"],
            "lng": a["lng"],
            "road_id": a.get("road_id"),
            "reference_photo_key": a.get("reference_photo_key"),
            "provenance": a.get("provenance", "simulated"),
            "source": "seed",
            "seeded": True,
            "created_at": now_iso,
        }
        table_assets.put_item(Item=float_to_decimal(item))
    print(f"[+] Successfully seeded {len(assets)} assets.")

    # 2. Seed Case 1: CS-SEED01 (minto_bridge, AWAITING_FIX, rung 2)
    mb = hotspots.get("minto_bridge", {})
    t1 = (now - timedelta(hours=2)).isoformat()
    t2 = (now - timedelta(minutes=45)).isoformat()
    case1 = {
        "case_id": "CS-SEED01",
        "hotspot_id": "minto_bridge",
        "asset_id": "ASSET-001",
        "lat": mb.get("lat", 28.6330),
        "lng": mb.get("lng", 77.2200),
        "status": "AWAITING_FIX",
        "rung": 2,
        "owner": "PWD",
        "jurisdiction": mb.get("jurisdiction"),
        "warranty": mb.get("warranty"),
        "analysis": {
            "hazard_type": "open_manhole",
            "severity": 4,
            "submerged": True,
            "confidence": 0.88,
            "description": "Submerged open sewer manhole near underpass entry",
            "visible_evidence": "Circular surface disruption under standing water",
        },
        "photo_key": None,
        "execution_arn": None,
        "timer_profile": "demo",
        "dry_run": True,
        "seeded": True,
        "demo_run": False,
        "created_at": t1,
        "updated_at": t2,
    }
    table_cases.put_item(Item=float_to_decimal(case1))
    table_events.put_item(Item=float_to_decimal({
        "case_id": "CS-SEED01",
        "ts_seq": f"{t1}#0001",
        "type": "NOTICE_SENT",
        "message": "Notice sent to Executive Engineer, PWD Division (illustrative)",
        "rung": 1,
        "meta": {"recipient_role": "Executive Engineer, PWD Division (illustrative)", "generated_by": "template_fallback"},
    }))
    table_events.put_item(Item=float_to_decimal({
        "case_id": "CS-SEED01",
        "ts_seq": f"{t2}#0002",
        "type": "REMINDER_SENT",
        "message": "Rung 2 reminder notice dispatched to Nodal Officer under the Flood Control Order",
        "rung": 2,
        "meta": {"recipient_role": "Nodal Officer under the Flood Control Order (illustrative)", "generated_by": "template_fallback"},
    }))

    # 3. Seed Case 2: CS-SEED02 (zakhira_underpass, ORPHAN, ESCALATED_DM, rung 4)
    zk = hotspots.get("zakhira_underpass", {})
    t3 = (now - timedelta(hours=5)).isoformat()
    case2 = {
        "case_id": "CS-SEED02",
        "hotspot_id": "zakhira_underpass",
        "asset_id": "ASSET-004",
        "lat": zk.get("lat", 28.6623),
        "lng": zk.get("lng", 77.1480),
        "status": "ESCALATED_DM",
        "rung": 4,
        "owner": "ORPHAN",
        "jurisdiction": zk.get("jurisdiction"),
        "warranty": zk.get("warranty"),
        "analysis": {
            "hazard_type": "waterlogging",
            "severity": 5,
            "submerged": True,
            "confidence": 0.95,
            "description": "Severe underpass ponding with disputed railway/civic boundary",
            "visible_evidence": "Submerged carriageway up to vehicle wheel arches",
        },
        "photo_key": None,
        "execution_arn": None,
        "timer_profile": "demo",
        "dry_run": True,
        "seeded": True,
        "demo_run": False,
        "created_at": t3,
        "updated_at": t3,
    }
    table_cases.put_item(Item=float_to_decimal(case2))
    table_events.put_item(Item=float_to_decimal({
        "case_id": "CS-SEED02",
        "ts_seq": f"{t3}#0001",
        "type": "ESCALATED",
        "message": "Notice dispatched to District Magistrate (illustrative) to convene agencies on disputed road",
        "rung": 4,
        "meta": {"recipient_role": "District Magistrate (illustrative)", "generated_by": "template_fallback"},
    }))

    # 4. Seed Case 3: CS-SEED03 (moolchand, CLOSED_VERIFIED, rung 1)
    mc = hotspots.get("moolchand", {})
    t4 = (now - timedelta(hours=8)).isoformat()
    t5 = (now - timedelta(hours=6)).isoformat()
    t6 = (now - timedelta(hours=4)).isoformat()
    case3 = {
        "case_id": "CS-SEED03",
        "hotspot_id": "moolchand",
        "asset_id": "ASSET-006",
        "lat": mc.get("lat", 28.5683),
        "lng": mc.get("lng", 77.2347),
        "status": "CLOSED_VERIFIED",
        "rung": 1,
        "owner": "PWD",
        "jurisdiction": mc.get("jurisdiction"),
        "warranty": mc.get("warranty"),
        "analysis": {
            "hazard_type": "pothole",
            "severity": 3,
            "submerged": False,
            "confidence": 0.82,
            "description": "Pothole in outer lane repaired and verified",
            "visible_evidence": "Asphalt depression with clear boundaries",
        },
        "photo_key": None,
        "execution_arn": None,
        "timer_profile": "demo",
        "dry_run": True,
        "seeded": True,
        "demo_run": False,
        "created_at": t4,
        "updated_at": t6,
    }
    table_cases.put_item(Item=float_to_decimal(case3))
    table_events.put_item(Item=float_to_decimal({
        "case_id": "CS-SEED03",
        "ts_seq": f"{t4}#0001",
        "type": "NOTICE_SENT",
        "message": "Notice sent to Executive Engineer, PWD Division (illustrative)",
        "rung": 1,
        "meta": {"recipient_role": "Executive Engineer, PWD Division (illustrative)", "generated_by": "template_fallback"},
    }))
    table_events.put_item(Item=float_to_decimal({
        "case_id": "CS-SEED03",
        "ts_seq": f"{t5}#0002",
        "type": "FIX_CLAIMED",
        "message": "Claimant submitted repair photo",
        "rung": 1,
        "meta": {"distance_m": 4.5},
    }))
    table_events.put_item(Item=float_to_decimal({
        "case_id": "CS-SEED03",
        "ts_seq": f"{t6}#0003",
        "type": "CLOSURE_VERIFIED",
        "message": "Closure verified by Nova: repair smooth asphalt verified",
        "rung": 1,
        "meta": {"verified": True},
    }))

    print("[+] Successfully seeded 3 demo cases with complete audit events.")


if __name__ == "__main__":
    main()
