from datetime import datetime, timezone
import json
import os
import traceback
import urllib.request
import boto3

from common.data_loader import get_hotspots, get_assets
from common.risk import score_hotspot, hazard_under_water, get_model_params

s3_client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))


def fetch_open_meteo_rain() -> tuple[float, float]:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=28.6139&longitude=77.2090"
        "&hourly=precipitation"
        "&past_hours=24"
        "&forecast_hours=3"
        "&timezone=UTC"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ArgusDelhi/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    hourly_precip = data.get("hourly", {}).get("precipitation", [])
    # hourly_precip contains 24 past hours + current/next hours.
    # The first 24 items correspond to past_hours=24
    if len(hourly_precip) >= 27:
        past_24 = hourly_precip[:24]
        next_3 = hourly_precip[24:27]
    elif len(hourly_precip) >= 24:
        past_24 = hourly_precip[:24]
        next_3 = hourly_precip[24:]
    else:
        past_24 = hourly_precip
        next_3 = [0.0]

    rain_prev24 = sum(float(x) for x in past_24 if x is not None)
    rain_3h = sum(float(x) for x in next_3 if x is not None)
    return round(rain_3h, 2), round(rain_prev24, 2)


def get_traffic_slowdown(lat: float, lng: float) -> float:
    enable_tomtom = os.environ.get("ENABLE_TOMTOM", "false").lower() == "true"
    api_key = os.environ.get("TOMTOM_API_KEY", "")
    if not enable_tomtom or not api_key:
        return 0.0

    try:
        url = (
            f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            f"?point={lat},{lng}&key={api_key}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ArgusDelhi/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            flow = data.get("flowSegmentData", {})
            curr_speed = float(flow.get("currentSpeed", 1.0))
            free_speed = float(flow.get("freeFlowSpeed", 1.0))
            if free_speed <= 0:
                return 0.0
            slowdown = max(0.0, min(1.0, 1.0 - (curr_speed / free_speed)))
            return round(slowdown, 4)
    except Exception as e:
        print(f"TomTom flowSegmentData error at ({lat}, {lng}): {e}")
        return 0.0


def handler(event, context):
    try:
        bucket = os.environ.get("BUCKET")
        if not bucket:
            print("BUCKET environment variable not set")
            return {"status": "error", "message": "Missing BUCKET"}

        rain_3h, rain_prev24 = fetch_open_meteo_rain()

        hotspots = get_hotspots()
        assets = get_assets()
        params = get_model_params()

        scores = []
        for h in hotspots:
            traffic = get_traffic_slowdown(float(h["lat"]), float(h["lng"]))
            score = score_hotspot(h, rain_3h, rain_prev24, traffic, params=params)
            prob = score["probability"]
            huw = hazard_under_water(h, assets, prob)
            score["hazard_under_water"] = huw
            scores.append(score)

        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "mode": "live",
            "generated_at": now_iso,
            "inputs": {
                "rain_3h_mm": rain_3h,
                "rain_prev24h_mm": rain_prev24,
                "traffic_slowdown": 0.0,
                "source": "open_meteo_live",
            },
            "model": {
                "version": params.get("version", "expert-prior-v1"),
                "fitted": params.get("fitted", False),
            },
            "scores": scores,
        }

        s3_client.put_object(
            Bucket=bucket,
            Key="exports/latest_scores.json",
            Body=json.dumps(payload, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        print(f"Successfully generated and saved live scores with rain_3h={rain_3h}, rain_prev24={rain_prev24}")
        return {"status": "ok", "scores_count": len(scores)}

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
