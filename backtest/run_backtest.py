import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
import boto3

# Ensure layer is importable
sys.path.insert(0, os.path.abspath("backend/layer/python"))
from common.data_loader import load_hotspots
from common.risk import score_hotspot


def fetch_event_rainfall(event_date: str) -> tuple[float, float]:
    """Fetches archive rainfall for Delhi for the event date and previous day from Open-Meteo."""
    dt = datetime.strptime(event_date, "%Y-%m-%d").date()
    prev_dt = dt - timedelta(days=1)

    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude=28.6139&longitude=77.2090&"
        f"start_date={prev_dt.isoformat()}&end_date={dt.isoformat()}&"
        f"hourly=precipitation&timezone=UTC"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "ArgusDelhi/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    hourly = data.get("hourly", {}).get("precipitation", [])
    # 48 hours total: first 24 for prev day, next 24 for event day
    prev_24h_vals = hourly[:24] if len(hourly) >= 24 else hourly
    curr_24h_vals = hourly[24:] if len(hourly) >= 48 else hourly

    rain_prev24h_mm = sum(prev_24h_vals)

    # Max 3h rolling sum on event day
    max_3h = 0.0
    for i in range(len(curr_24h_vals) - 2):
        window_sum = sum(curr_24h_vals[i : i + 3])
        if window_sum > max_3h:
            max_3h = window_sum

    return round(max_3h, 2), round(rain_prev24h_mm, 2)


def main():
    parser = argparse.ArgumentParser(description="Run historical monsoon waterlogging backtest replay")
    parser.add_argument("--events", default="backtest/events.json", help="Path to events.json")
    parser.add_argument("--out-dir", default="backtest/results", help="Path to output directory")
    args = parser.parse_args()

    if not os.path.exists(args.events):
        print(f"[!] Events file '{args.events}' does not exist.")
        sys.exit(0)

    with open(args.events, "r", encoding="utf-8") as f:
        all_events = json.load(f)

    valid_events = [
        ev for ev in all_events
        if ev.get("status") != "PLACEHOLDER" and ev.get("source_urls") and len(ev.get("source_urls")) > 0
    ]

    if not valid_events:
        print("[!] No real events configured in backtest/events.json (all events are PLACEHOLDER or missing source_urls).")
        print("    Please replace placeholders with 3-5 real news events with source URLs.")
        sys.exit(0)

    hotspots = load_hotspots()
    total_n = len(hotspots)
    evaluated_events = []

    for ev in valid_events:
        event_id = ev["event_id"]
        date_str = ev["date"]
        print(f"[*] Processing backtest event {event_id} ({date_str})...")

        try:
            rain_3h, rain_prev24h = fetch_event_rainfall(date_str)
        except Exception as e:
            print(f"[!] Warning: Could not fetch archive rainfall for {date_str}: {e}. Skipping.")
            continue

        reported_ids = set(ev.get("reported_hotspot_ids", []))

        # Score all hotspots
        scores = []
        for hs in hotspots:
            score = score_hotspot(hs, rain_3h_mm=rain_3h, rain_prev24h_mm=rain_prev24h, traffic_slowdown=0.0)
            scores.append({
                "hotspot_id": hs["hotspot_id"],
                "name": hs["name"],
                "probability": score["probability"],
                "reported_hit": hs["hotspot_id"] in reported_ids,
            })

        scores.sort(key=lambda s: s["probability"], reverse=True)
        top_20 = scores[:20]

        top_20_ids = [s["hotspot_id"] for s in top_20]
        hits = sum(1 for s in top_20 if s["reported_hit"])

        precision_at_20 = round(hits / min(20, total_n), 4) if total_n > 0 else 0.0
        recall = round(hits / len(reported_ids), 4) if len(reported_ids) > 0 else None
        random_baseline = round(len(reported_ids) / total_n, 4) if total_n > 0 else 0.0

        evaluated_events.append({
            "event_id": event_id,
            "date": date_str,
            "description": ev.get("description", ""),
            "held_out": ev.get("held_out", False),
            "reported_hotspot_ids": list(reported_ids),
            "reported_other_count": ev.get("reported_other_count", 0),
            "top20_predicted": top_20_ids,
            "top_20": top_20,
            "precision_at_20": precision_at_20,
            "recall": recall,
            "random_baseline_precision": random_baseline,
            "inputs": {
                "rain_3h_mm": rain_3h,
                "rain_prev24h_mm": rain_prev24h,
            },
        })

    os.makedirs(args.out_dir, exist_ok=True)
    out_file = os.path.join(args.out_dir, "backtest.json")
    results = {"events": evaluated_events, "generated_at": datetime.now(timezone.utc).isoformat()}

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[+] Wrote backtest results to {out_file} ({len(evaluated_events)} events evaluated).")

    bucket = os.environ.get("BUCKET")
    if bucket:
        try:
            s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))
            s3.put_object(
                Bucket=bucket,
                Key="eval/backtest.json",
                Body=json.dumps(results, indent=2),
                ContentType="application/json",
            )
            print(f"[+] Uploaded backtest results to s3://{bucket}/eval/backtest.json")
        except Exception as e:
            print(f"[!] S3 upload warning: {e}")


if __name__ == "__main__":
    main()
