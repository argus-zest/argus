from datetime import datetime, timezone
import json
import os
import traceback
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from common.data_loader import get_hotspots, get_assets
from common.http import ok, err
from common.risk import score_hotspot, hazard_under_water, get_model_params

s3_client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def _handle_live_mode() -> Dict[str, Any]:
    bucket = os.environ.get("BUCKET")
    if not bucket:
        return err(502, "MODEL_ERROR", "Live scores not available yet")

    try:
        resp = s3_client.get_object(Bucket=bucket, Key="exports/latest_scores.json")
        payload = json.loads(resp["Body"].read().decode("utf-8"))
        return ok(payload)
    except (ClientError, Exception) as e:
        return err(502, "MODEL_ERROR", "Live scores not available yet")


def handler(event, context):
    try:
        q_params = event.get("queryStringParameters") or {}
        mode = q_params.get("mode", "whatif").lower()

        if mode == "live":
            return _handle_live_mode()

        try:
            rain_3h = float(q_params.get("rain_3h_mm", 0.0))
            rain_prev24 = float(q_params.get("rain_prev24h_mm", 0.0))
            traffic = float(q_params.get("traffic_slowdown", 0.0))
        except (ValueError, TypeError) as e:
            return err(400, "BAD_REQUEST", f"Invalid numeric parameter: {str(e)}")

        hotspots = get_hotspots()
        assets = get_assets()
        params = get_model_params()

        scores = []
        for h in hotspots:
            score = score_hotspot(h, rain_3h, rain_prev24, traffic, params=params)
            prob = score["probability"]
            huw = hazard_under_water(h, assets, prob)
            score["hazard_under_water"] = huw
            scores.append(score)

        now_iso = datetime.now(timezone.utc).isoformat()
        response_body = {
            "mode": "whatif",
            "generated_at": now_iso,
            "inputs": {
                "rain_3h_mm": rain_3h,
                "rain_prev24h_mm": rain_prev24,
                "traffic_slowdown": traffic,
                "source": "user_simulation",
            },
            "model": {
                "version": params.get("version", "expert-prior-v1"),
                "fitted": params.get("fitted", False),
            },
            "scores": scores,
        }
        return ok(response_body)

    except ValueError as e:
        return err(400, "BAD_REQUEST", str(e))
    except Exception as e:
        traceback.print_exc()
        return err(500, "INTERNAL", f"Internal error: {str(e)}")
