import json
from datetime import date
from pathlib import Path

from jsonschema import validate

from scripts.seed_demo import enriched_hotspots


def openapi_nullable_schema(value):
    """JSON Schema does not implement OpenAPI 3.0's nullable keyword."""
    if isinstance(value, list):
        return [openapi_nullable_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: openapi_nullable_schema(item) for key, item in value.items()}
    if result.get('nullable') and isinstance(result.get('type'), str):
        result['type'] = [result['type'], 'null']
    return result


def test_seeded_hotspots_include_contract_valid_jurisdiction_and_warranty():
    hotspots = enriched_hotspots(date(2026, 10, 11))
    root = Path(__file__).resolve().parents[1]
    for key, schema_name in [('jurisdiction', 'Jurisdiction'), ('warranty', 'Warranty')]:
        schema = openapi_nullable_schema(json.loads(
            (root / 'contracts' / 'schemas' / f'{schema_name}.json').read_text(),
        ))
        for hotspot_id in ['minto_bridge', 'zakhira_underpass', 'moolchand']:
            assert hotspots[hotspot_id][key] is not None
            validate(hotspots[hotspot_id][key], schema)
