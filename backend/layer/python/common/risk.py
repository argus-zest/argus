import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional
from common.geo import haversine_m

_PARAMS_CACHE: Optional[Dict[str, Any]] = None


def get_model_params() -> Dict[str, Any]:
    global _PARAMS_CACHE
    if _PARAMS_CACHE is not None:
        return _PARAMS_CACHE

    params_path = Path(__file__).resolve().parent.parent / "civic_data" / "model_params.json"
    if params_path.exists():
        with open(params_path, "r", encoding="utf-8") as f:
            _PARAMS_CACHE = json.load(f)
    else:
        _PARAMS_CACHE = {
            "version": "expert-prior-v1",
            "fitted": False,
            "static": {
                "bias": -2.2,
                "w_depression": 0.9,
                "w_low_rel_elev": 0.8,
                "w_underpass": 1.4,
                "w_news": 0.5,
                "norm": {
                    "depression_m": {"mean": 0.0, "std": 1.0},
                    "rel_elev_m": {"mean": 0.0, "std": 1.0},
                },
            },
            "event": {
                "a_susceptibility": 3.0,
                "b_rain3h": 1.1,
                "c_rain24h": 0.5,
                "d_traffic": 1.0,
                "bias": -6.5,
            },
            "bands": [
                [0.0, 0.25, "low"],
                [0.25, 0.5, "moderate"],
                [0.5, 0.75, "high"],
                [0.75, 1.01, "severe"],
            ],
        }
    return _PARAMS_CACHE


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _clip(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))


def get_band(probability: float, bands: List[List[Any]]) -> str:
    for low, high, label in bands:
        if low <= probability < high:
            return label
    return bands[-1][2]


def score_hotspot(
    hotspot: Dict[str, Any],
    rain_3h_mm: float,
    rain_prev24h_mm: float,
    traffic_slowdown: float,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Input validation per SPEC 5.2
    if not (0.0 <= rain_3h_mm <= 200.0):
        raise ValueError(f"rain_3h_mm must be between 0 and 200, got {rain_3h_mm}")
    if not (0.0 <= rain_prev24h_mm <= 300.0):
        raise ValueError(f"rain_prev24h_mm must be between 0 and 300, got {rain_prev24h_mm}")
    if not (0.0 <= traffic_slowdown <= 1.0):
        raise ValueError(f"traffic_slowdown must be between 0 and 1, got {traffic_slowdown}")

    p = params or get_model_params()
    static = p["static"]
    event = p["event"]
    norm = static["norm"]

    features = hotspot.get("features", {})
    dep_m = features.get("depression_m")
    rel_m = features.get("rel_elev_m")
    underpass = bool(features.get("underpass", False))
    news_count = features.get("news_events_count")

    # z_dep: null -> 0
    mean_dep = norm["depression_m"]["mean"]
    std_dep = max(norm["depression_m"]["std"], 0.1)
    if dep_m is not None:
        z_dep = _clip((dep_m - mean_dep) / std_dep, -3.0, 3.0)
        dep_missing = False
    else:
        z_dep = 0.0
        dep_missing = True

    # z_low: null -> 0; lower ground => higher risk
    mean_rel = norm["rel_elev_m"]["mean"]
    std_rel = max(norm["rel_elev_m"]["std"], 0.1)
    if rel_m is not None:
        z_low = _clip(-(rel_m - mean_rel) / std_rel, -3.0, 3.0)
        low_missing = False
    else:
        z_low = 0.0
        low_missing = True

    c_dep = static["w_depression"] * z_dep
    c_low = static["w_low_rel_elev"] * z_low
    c_underpass = static["w_underpass"] * (1.0 if underpass else 0.0)

    news_val = news_count if news_count is not None else 0
    c_news = static["w_news"] * math.log(1.0 + news_val)
    news_missing = (news_count is None)

    s_logit = static["bias"] + c_dep + c_low + c_underpass + c_news
    S = _sigmoid(s_logit)

    c_susc = event["a_susceptibility"] * S
    c_rain3 = event["b_rain3h"] * math.log(1.0 + rain_3h_mm)
    c_rain24 = event["c_rain24h"] * math.log(1.0 + rain_prev24h_mm)
    c_traffic = event["d_traffic"] * traffic_slowdown

    event_logit = event["bias"] + c_susc + c_rain3 + c_rain24 + c_traffic
    P = _sigmoid(event_logit)
    P_rounded = round(P, 4)

    drivers = [
        {"name": "depression", "contribution": round(c_dep, 4), "missing": dep_missing},
        {"name": "low_elevation", "contribution": round(c_low, 4), "missing": low_missing},
        {"name": "underpass", "contribution": round(c_underpass, 4), "missing": False},
        {"name": "news_events", "contribution": round(c_news, 4), "missing": news_missing},
        {"name": "susceptibility", "contribution": round(c_susc, 4), "missing": False},
        {"name": "rain_3h", "contribution": round(c_rain3, 4), "missing": False},
        {"name": "rain_prev24h", "contribution": round(c_rain24, 4), "missing": False},
        {"name": "traffic", "contribution": round(c_traffic, 4), "missing": False},
    ]

    drivers.sort(key=lambda d: abs(d["contribution"]), reverse=True)

    band = get_band(P_rounded, p["bands"])

    return {
        "hotspot_id": hotspot.get("hotspot_id", ""),
        "susceptibility": round(S, 4),
        "probability": P_rounded,
        "band": band,
        "drivers": drivers,
    }


def hazard_under_water(
    hotspot: Dict[str, Any],
    assets: List[Dict[str, Any]],
    probability: float,
) -> Dict[str, Any]:
    base_weights = {
        "open_manhole": 1.0,
        "missing_drain_cover": 1.0,
        "pothole": 0.5,
    }

    h_lat = hotspot["lat"]
    h_lng = hotspot["lng"]

    matching_asset_ids = []
    total_val = 0.0

    for asset in assets:
        a_lat = asset["lat"]
        a_lng = asset["lng"]
        dist = haversine_m(h_lat, h_lng, a_lat, a_lng)
        if dist <= 50.0:
            a_type = asset.get("type", "pothole")
            severity = float(asset.get("severity", 1))
            base = base_weights.get(a_type, 0.5)
            total_val += base * (severity / 5.0)
            matching_asset_ids.append(asset.get("asset_id", ""))

    weight = min(1.0, total_val)
    score = round(probability * weight, 4)

    return {
        "score": score,
        "weight": round(weight, 4),
        "asset_ids": matching_asset_ids,
    }
