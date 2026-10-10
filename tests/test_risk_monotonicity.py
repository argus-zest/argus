import pytest
import json
from backend.functions.risk.app import handler

def test_risk_handler_monotonicity_rain_0_to_100():
    for r24 in [0, 20]:
        for hs_idx in range(10):
            prev_prob = -1.0
            for rain_3h in range(0, 105, 10):
                event = {
                    'queryStringParameters': {
                        'rain_3h_mm': str(rain_3h),
                        'rain_prev24h_mm': str(r24),
                        'traffic_slowdown': '0.1'
                    }
                }
                res = handler(event, None)
                body = json.loads(res['body'])
                prob = body['scores'][hs_idx]['probability']
                assert prob >= prev_prob - 1e-9, f"Monotonicity failed at hotspot index {hs_idx}, rain {rain_3h}"
                prev_prob = prob
