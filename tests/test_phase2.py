import json
from unittest.mock import patch, MagicMock
import io
import pytest

# Ensure backend/layer/python is importable
from backend.functions.health.app import handler as health_handler
from backend.functions.hotspots.app import handler as hotspots_handler
from backend.functions.risk.app import handler as risk_handler
from backend.functions.assets.app import handler as assets_handler
from backend.functions.eval_results.app import handler as eval_results_handler
from backend.functions.scheduled_score.app import handler as scheduled_score_handler


def test_health_handler():
    res = health_handler({}, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["status"] == "ok"
    assert "time" in body


def test_hotspots_handler_get():
    event = {
        "rawPath": "/v1/hotspots",
        "requestContext": {"http": {"method": "GET"}},
    }
    res = hotspots_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert "hotspots" in body
    assert len(body["hotspots"]) >= 10

    first = body["hotspots"][0]
    assert "road" in first
    assert "jurisdiction" in first
    assert "warranty" in first
    assert "assets" in first
    assert first["jurisdiction"]["owner"] in ["NHAI", "NDMC", "PWD", "DJB", "MCD", "ORPHAN"]


def test_hotspots_handler_resolve():
    event = {
        "rawPath": "/v1/resolve",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"lat": 28.6330, "lng": 77.2200, "asset_type": "open_manhole"}),
    }
    res = hotspots_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert "jurisdiction" in body
    assert "warranty" in body
    # open_manhole on Minto road resolves to DJB
    assert body["jurisdiction"]["owner"] == "DJB"


def test_risk_handler_whatif_validation():
    event = {
        "queryStringParameters": {
            "mode": "whatif",
            "rain_3h_mm": "50",
            "rain_prev24h_mm": "30",
            "traffic_slowdown": "0.25",
        }
    }
    res = risk_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["mode"] == "whatif"
    assert "scores" in body
    assert len(body["scores"]) >= 10

    for score in body["scores"]:
        assert 0.0 <= score["probability"] <= 1.0
        assert score["band"] in ["low", "moderate", "high", "severe"]
        assert "hazard_under_water" in score
        assert 0.0 <= score["hazard_under_water"]["weight"] <= 1.0


def test_risk_handler_bad_input():
    event = {
        "queryStringParameters": {
            "rain_3h_mm": "250",  # exceeds 200 max
        }
    }
    res = risk_handler(event, None)
    assert res["statusCode"] == 400
    body = json.loads(res["body"])
    assert body["error"]["code"] == "BAD_REQUEST"


def test_risk_handler_live_mode_fallback():
    with patch("backend.functions.risk.app.s3_client") as mock_s3:
        mock_s3.get_object.side_effect = Exception("NoSuchKey")
        event = {"queryStringParameters": {"mode": "live"}}
        res = risk_handler(event, None)
        assert res["statusCode"] == 502
        body = json.loads(res["body"])
        assert body["error"]["code"] == "MODEL_ERROR"


def test_assets_handler():
    res = assets_handler({}, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert "assets" in body
    assert len(body["assets"]) == 8


def test_eval_results_handler():
    with patch("backend.functions.eval_results.app.s3_client") as mock_s3:
        mock_s3.get_object.side_effect = Exception("NoSuchKey")
        res = eval_results_handler({}, None)
        assert res["statusCode"] == 200
        body = json.loads(res["body"])
        assert body["rdd2022"] is None
        assert body["backtest"] is None


def test_scheduled_score_handler():
    fake_weather_json = json.dumps({
        "hourly": {
            "precipitation": [0.5] * 24 + [2.0, 3.0, 1.0]
        }
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen, \
         patch("backend.functions.scheduled_score.app.s3_client") as mock_s3, \
         patch.dict("os.environ", {"BUCKET": "test-bucket"}):

        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_weather_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = scheduled_score_handler({}, None)
        assert res["status"] == "ok"
        assert res["scores_count"] >= 10
        assert mock_s3.put_object.called
