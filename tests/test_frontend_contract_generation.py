from pathlib import Path

from scripts.generate_frontend_schemas import generate


def test_frontend_validators_match_the_contract_and_handler_adapters():
    artifact = Path(__file__).resolve().parents[1] / 'frontend/src/lib/response-schemas.ts'
    assert artifact.read_text() == generate()


def test_restored_client_accepts_actual_read_handler_responses(monkeypatch):
    """Exercise both sides locally without network, AWS calls, or fabricated inference."""
    import importlib.util
    import json
    import shutil
    import subprocess
    from unittest.mock import patch

    import pytest

    if not shutil.which('node'):
        pytest.skip('Node is required for the browser-client runtime boundary check')
    root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv('TABLE_ASSETS', raising=False)

    def load(name):
        spec = importlib.util.spec_from_file_location(
            f'contract_boundary_{name}', root / f'backend/functions/{name}/app.py'
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    with patch('boto3.client'), patch('boto3.resource'):
        hotspots = load('hotspots')
        assets = load('assets')
        risk = load('risk')
        payloads = {
            '/v1/hotspots': json.loads(hotspots.handler({}, None)['body']),
            '/v1/assets': json.loads(assets.handler({}, None)['body']),
            '/v1/risk': json.loads(risk.handler({'queryStringParameters': {
                'mode': 'whatif', 'rain_3h_mm': '40',
                'rain_prev24h_mm': '30', 'traffic_slowdown': '0.3',
            }}, None)['body']),
            '/v1/resolve': json.loads(hotspots.handler({
                'rawPath': '/v1/resolve', 'body': json.dumps({'lat': 28.633, 'lng': 77.22}),
            }, None)['body']),
        }
    script = '''
import { createApiClient } from './frontend/src/lib/api.ts';
let input = '';
for await (const chunk of process.stdin) input += chunk;
const responses = JSON.parse(input);
const client = createApiClient({ fetch: async (url) =>
  new Response(JSON.stringify(responses[new URL(url, 'http://local.test').pathname])) });
await client.fetchHotspots();
await client.fetchAssets();
await client.fetchRisk('whatif', 40, 30, 30);
await client.resolveLocation(28.633, 77.22);
console.log('Actual read-handler envelopes accepted');
'''
    result = subprocess.run(['node', '--input-type=module', '-e', script],
                            cwd=root, input=json.dumps(payloads),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'envelopes accepted' in result.stdout
