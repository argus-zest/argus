from datetime import date
import traceback
from typing import Any, Dict

from common.data_loader import get_hotspots, get_roads, get_assets, get_contracts
from common.geo import haversine_m
from common.http import ok, err, parse_json, BadRequest
from common.jurisdiction import resolve_jurisdiction, road_for_point
from common.warranty import compute_warranty, find_latest_contract


def _handle_resolve(event: Dict[str, Any]) -> Dict[str, Any]:
    body = parse_json(event)
    lat = body.get("lat")
    lng = body.get("lng")
    if lat is None or lng is None:
        raise BadRequest("lat and lng are required")

    asset_type = body.get("asset_type")
    roads = get_roads()
    contracts = get_contracts()

    road = road_for_point(roads, float(lat), float(lng))
    jurisdiction = resolve_jurisdiction(road, asset_type)

    latest_contract = find_latest_contract(contracts, road["road_id"]) if road else None
    warranty = compute_warranty(latest_contract, as_of=date.today())

    return ok({
        "road": road,
        "jurisdiction": jurisdiction,
        "warranty": warranty,
    })


def _handle_get_hotspots() -> Dict[str, Any]:
    hotspots = get_hotspots()
    roads = get_roads()
    assets = get_assets()
    contracts = get_contracts()

    road_by_id = {r["road_id"]: r for r in roads}
    today = date.today()

    enriched = []
    for h in hotspots:
        road = road_by_id.get(h["road_id"], {})
        jurisdiction = resolve_jurisdiction(road, None)
        latest_contract = find_latest_contract(contracts, h["road_id"])
        warranty = compute_warranty(latest_contract, as_of=today)

        # Assets within 50m
        h_lat = float(h["lat"])
        h_lng = float(h["lng"])
        h_assets = [
            a for a in assets
            if haversine_m(h_lat, h_lng, float(a["lat"]), float(a["lng"])) <= 50.0
        ]

        item = dict(h)
        item["road"] = road
        item["jurisdiction"] = jurisdiction
        item["warranty"] = warranty
        item["assets"] = h_assets
        enriched.append(item)

    return ok({"hotspots": enriched})


def handler(event, context):
    try:
        raw_path = event.get("rawPath", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        if "resolve" in raw_path or method == "POST":
            return _handle_resolve(event)
        return _handle_get_hotspots()

    except BadRequest as e:
        return err(400, "BAD_REQUEST", str(e))
    except Exception as e:
        traceback.print_exc()
        return err(500, "INTERNAL", f"Internal error: {str(e)}")
