import math
from datetime import date
import pytest

from common.geo import haversine_m, nearest
from common.risk import score_hotspot, hazard_under_water, get_model_params
from common.jurisdiction import resolve_jurisdiction, road_for_point, OFFICER_ROLES
from common.warranty import compute_warranty, add_months, find_latest_contract
from common.http import ok, err, parse_json, BadRequest


def test_geo_haversine_and_nearest():
    # Delhi centre to Minto Bridge (~2.2 km)
    dist = haversine_m(28.6139, 77.2090, 28.6330, 77.2200)
    assert 2000 < dist < 2500

    items = [
        {"name": "far", "lat": 28.7, "lng": 77.3},
        {"name": "near", "lat": 28.6140, "lng": 77.2091},
    ]
    closest = nearest(items, 28.6139, 77.2090)
    assert closest["name"] == "near"


def test_risk_monotonic_rain_3h():
    hotspot = {
        "hotspot_id": "test_hs",
        "lat": 28.6,
        "lng": 77.2,
        "features": {"depression_m": 1.0, "rel_elev_m": -2.0, "underpass": True, "news_events_count": 2},
    }
    prev_prob = -1.0
    for rain in [0.0, 10.0, 25.0, 50.0, 80.0, 120.0, 200.0]:
        res = score_hotspot(hotspot, rain_3h_mm=rain, rain_prev24h_mm=10.0, traffic_slowdown=0.2)
        prob = res["probability"]
        assert prob >= prev_prob
        prev_prob = prob


def test_all_hotspots_monotonic_rain_0_to_100():
    from common.data_loader import load_hotspots
    hotspots = load_hotspots()
    assert len(hotspots) >= 10
    for hs in hotspots:
        prev_prob = -1.0
        for rain in range(0, 105, 10):
            res = score_hotspot(hs, rain_3h_mm=float(rain), rain_prev24h_mm=0.0, traffic_slowdown=0.0)
            prob = res["probability"]
            assert prob >= prev_prob, f"Hotspot {hs['hotspot_id']} failed monotonicity at rain={rain}"
            prev_prob = prob



def test_risk_monotonic_rain_prev24h():
    hotspot = {
        "hotspot_id": "test_hs",
        "lat": 28.6,
        "lng": 77.2,
        "features": {"depression_m": 0.5, "rel_elev_m": 0.0, "underpass": False, "news_events_count": 0},
    }
    prev_prob = -1.0
    for rain in [0.0, 20.0, 50.0, 100.0, 200.0, 300.0]:
        res = score_hotspot(hotspot, rain_3h_mm=20.0, rain_prev24h_mm=rain, traffic_slowdown=0.1)
        prob = res["probability"]
        assert prob >= prev_prob
        prev_prob = prob


def test_risk_monotonic_traffic():
    hotspot = {
        "hotspot_id": "test_hs",
        "lat": 28.6,
        "lng": 77.2,
        "features": {"depression_m": 0.0, "rel_elev_m": 1.0, "underpass": False, "news_events_count": None},
    }
    prev_prob = -1.0
    for traffic in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        res = score_hotspot(hotspot, rain_3h_mm=30.0, rain_prev24h_mm=30.0, traffic_slowdown=traffic)
        prob = res["probability"]
        assert prob >= prev_prob
        prev_prob = prob


def test_underpass_higher_susceptibility():
    hs_underpass = {
        "hotspot_id": "hs_up",
        "lat": 28.6,
        "lng": 77.2,
        "features": {"depression_m": 0.5, "rel_elev_m": -1.0, "underpass": True, "news_events_count": 1},
    }
    hs_surface = {
        "hotspot_id": "hs_surf",
        "lat": 28.6,
        "lng": 77.2,
        "features": {"depression_m": 0.5, "rel_elev_m": -1.0, "underpass": False, "news_events_count": 1},
    }
    res_up = score_hotspot(hs_underpass, 10.0, 10.0, 0.0)
    res_surf = score_hotspot(hs_surface, 10.0, 10.0, 0.0)

    assert res_up["susceptibility"] > res_surf["susceptibility"]
    assert res_up["probability"] > res_surf["probability"]


def test_risk_input_validation():
    hotspot = {"features": {}}
    with pytest.raises(ValueError):
        score_hotspot(hotspot, -1.0, 10.0, 0.0)
    with pytest.raises(ValueError):
        score_hotspot(hotspot, 201.0, 10.0, 0.0)
    with pytest.raises(ValueError):
        score_hotspot(hotspot, 10.0, -5.0, 0.0)
    with pytest.raises(ValueError):
        score_hotspot(hotspot, 10.0, 305.0, 0.0)
    with pytest.raises(ValueError):
        score_hotspot(hotspot, 10.0, 10.0, -0.1)
    with pytest.raises(ValueError):
        score_hotspot(hotspot, 10.0, 10.0, 1.1)


def test_hazard_under_water_cap():
    hotspot = {"lat": 28.6330, "lng": 77.2200}
    # Multiple high-severity assets near hotspot
    assets = [
        {"asset_id": "A1", "lat": 28.6331, "lng": 77.2201, "type": "open_manhole", "severity": 5}, # 1.0 * 1.0 = 1.0
        {"asset_id": "A2", "lat": 28.6330, "lng": 77.2202, "type": "open_manhole", "severity": 5}, # 1.0
        {"asset_id": "A3", "lat": 28.6329, "lng": 77.2200, "type": "missing_drain_cover", "severity": 5}, # 1.0
    ]
    res = hazard_under_water(hotspot, assets, probability=0.8)
    assert res["weight"] == 1.0
    assert res["score"] == 0.8
    assert len(res["asset_ids"]) == 3


def test_jurisdiction_rules_in_exact_order():
    # Rule 1: road is None -> ORPHAN, 0.30, start_rung 4
    j1 = resolve_jurisdiction(None, None)
    assert j1["owner"] == "ORPHAN"
    assert j1["confidence"] == 0.30
    assert j1["start_rung"] == 4
    assert j1["officer_role"] == OFFICER_ROLES["ORPHAN"]
    assert "No road record" in j1["reasons"][0]

    # Rule 2: disputed -> ORPHAN, 0.40, start_rung 4
    road_disputed = {"name": "Disputed Lane", "ownership_disputed": True, "is_national_highway": True, "width_ft": 100}
    j2 = resolve_jurisdiction(road_disputed, None)
    assert j2["owner"] == "ORPHAN"
    assert j2["confidence"] == 0.40
    assert j2["start_rung"] == 4
    assert "disputed" in j2["reasons"][0].lower()

    # Rule 3: national highway -> NHAI, 0.90, start_rung 1
    road_nh = {"name": "NH-48", "ownership_disputed": False, "is_national_highway": True, "in_ndmc": True, "width_ft": 120}
    j3 = resolve_jurisdiction(road_nh, "open_manhole")
    assert j3["owner"] == "NHAI"
    assert j3["confidence"] == 0.90
    assert j3["start_rung"] == 1
    assert j3["officer_role"] == OFFICER_ROLES["NHAI"]

    # Rule 4: in_ndmc -> NDMC, 0.85, start_rung 1
    road_ndmc = {"name": "Barakhamba Road", "ownership_disputed": False, "is_national_highway": False, "in_ndmc": True, "width_ft": 80}
    j4 = resolve_jurisdiction(road_ndmc, "open_manhole")
    assert j4["owner"] == "NDMC"
    assert j4["confidence"] == 0.85
    assert j4["start_rung"] == 1
    assert j4["officer_role"] == OFFICER_ROLES["NDMC"]

    # Rule 5: open_manhole -> DJB, 0.70, start_rung 1
    road_pwd_width = {"name": "Broad Avenue", "ownership_disputed": False, "is_national_highway": False, "in_ndmc": False, "width_ft": 80}
    j5 = resolve_jurisdiction(road_pwd_width, "open_manhole")
    assert j5["owner"] == "DJB"
    assert j5["confidence"] == 0.70
    assert j5["start_rung"] == 1
    assert j5["officer_role"] == OFFICER_ROLES["DJB"]
    assert "Delhi Jal Board" in j5["reasons"][0]

    # Rule 6: width_ft >= 60 -> PWD, 0.80, start_rung 1
    j6 = resolve_jurisdiction(road_pwd_width, "pothole")
    assert j6["owner"] == "PWD"
    assert j6["confidence"] == 0.80
    assert j6["start_rung"] == 1
    assert j6["officer_role"] == OFFICER_ROLES["PWD"]

    # Rule 7: Otherwise -> MCD, 0.60, start_rung 1
    road_mcd = {"name": "Narrow Street", "ownership_disputed": False, "is_national_highway": False, "in_ndmc": False, "width_ft": 40}
    j7 = resolve_jurisdiction(road_mcd, "pothole")
    assert j7["owner"] == "MCD"
    assert j7["confidence"] == 0.60
    assert j7["start_rung"] == 1
    assert j7["officer_role"] == OFFICER_ROLES["MCD"]


def test_warranty_month_end_boundaries():
    # Case A: completion 2021-02-28 + 60 months -> 2026-02-28
    c1 = {"completion_date": "2021-02-28", "defect_liability_months": 60, "contractor_label": "Contractor A (demo)"}
    w1 = compute_warranty(c1, as_of=date(2026, 1, 1))
    assert w1["end_date"] == "2026-02-28"
    assert w1["status"] == "in_warranty"
    assert w1["days_remaining"] == (date(2026, 2, 28) - date(2026, 1, 1)).days

    # Case B: completion 2020-08-31 + 6 months -> 2021-02-28
    c2 = {"completion_date": "2020-08-31", "defect_liability_months": 6, "contractor_label": "Contractor B (demo)"}
    w2 = compute_warranty(c2, as_of=date(2026, 10, 11))
    assert w2["end_date"] == "2021-02-28"
    assert w2["status"] == "expired"
    assert w2["days_remaining"] < 0

    # Case C: null contract
    w3 = compute_warranty(None, as_of=date(2026, 10, 11))
    assert w3["status"] == "unknown"
    assert w3["end_date"] is None
    assert w3["days_remaining"] == 0


def test_http_helpers():
    resp_ok = ok({"foo": "bar"}, 200)
    assert resp_ok["statusCode"] == 200
    assert '"foo": "bar"' in resp_ok["body"]

    resp_err = err(400, "BAD_REQUEST", "Invalid param")
    assert resp_err["statusCode"] == 400
    assert '"BAD_REQUEST"' in resp_err["body"]

    assert parse_json({"body": '{"a": 1}'}) == {"a": 1}
    with pytest.raises(BadRequest):
        parse_json({"body": "invalid json"})
    with pytest.raises(BadRequest):
        parse_json({})
