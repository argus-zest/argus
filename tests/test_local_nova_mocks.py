from unittest.mock import patch

import pytest

from common.nova import (
    NovaError, analyze_hazard, converse, extract_clause, get_bedrock_client, verify_fix,
)


@pytest.fixture
def local_mocks(monkeypatch):
    monkeypatch.setenv('USE_MOCKS', 'true')
    monkeypatch.setenv('ARGUS_ENV', 'local')
    monkeypatch.delenv('AWS_LAMBDA_FUNCTION_NAME', raising=False)
    monkeypatch.delenv('AWS_EXECUTION_ENV', raising=False)
    monkeypatch.delenv('AWS_SAM_LOCAL', raising=False)


def test_local_fixtures_are_marked_and_never_invoke(local_mocks):
    with patch('common.nova.get_bedrock_client') as client:
        analysis = analyze_hazard(b'local-test', 'jpeg')
        repair = verify_fix(None, b'local-test', 'pothole')
        clause = extract_clause(b'local-test', 'tender.pdf')
        client.assert_not_called()
    for result in (analysis, repair, clause):
        assert result['mock'] is True
        assert result['source'] == 'local_mock'
    assert analysis['hazard_type'] == 'unclear'
    assert analysis['confidence'] == 0
    assert repair['hazard_still_present'] is True
    assert repair['confidence'] == 0
    assert clause['found'] is False
    assert clause['verified_in_text'] is False


@pytest.mark.parametrize('variable,value', [
    ('ARGUS_ENV', 'production'),
    ('AWS_LAMBDA_FUNCTION_NAME', 'argus-analyze'),
    ('AWS_EXECUTION_ENV', 'AWS_Lambda_python3.12'),
    ('USE_MOCKS', 'invalid'),
])
def test_mock_configuration_cannot_enable_production_fixtures(local_mocks, monkeypatch, variable, value):
    monkeypatch.setenv(variable, value)
    with patch('common.nova.get_bedrock_client') as client:
        with pytest.raises(NovaError, match='Mock|USE_MOCKS') as error:
            analyze_hazard(b'test', 'jpeg')
        assert error.value.code == 'MOCK_CONFIGURATION'
        client.assert_not_called()


def test_sam_local_can_use_explicit_local_mode(local_mocks, monkeypatch):
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME', 'argus-analyze')
    monkeypatch.setenv('AWS_SAM_LOCAL', 'true')
    assert analyze_hazard(b'test', 'png')['mock'] is True


def test_untyped_converse_does_not_fabricate_agent_inference(local_mocks):
    with patch('common.nova.get_bedrock_client') as client:
        with pytest.raises(NovaError) as error:
            converse([], 'test')
        assert error.value.code == 'LOCAL_MOCK_UNSUPPORTED'
        client.assert_not_called()


def test_mock_mode_still_validates_images(local_mocks):
    with pytest.raises(NovaError) as error:
        analyze_hazard(b'test', 'gif')
    assert error.value.code == 'BAD_REQUEST'
    with pytest.raises(NovaError) as error:
        verify_fix(None, b'x' * (4 * 1024 * 1024), 'pothole')
    assert error.value.code == 'IMAGE_TOO_LARGE'


def test_region_override_is_rejected_before_client_creation(monkeypatch):
    monkeypatch.setenv('AWS_REGION', 'ap-southeast-1')
    with patch('common.nova.boto3.client') as client:
        with pytest.raises(NovaError) as error:
            get_bedrock_client()
        assert error.value.code == 'REGION_POLICY'
        client.assert_not_called()


def test_analysis_handler_exposes_mock_identification(local_mocks):
    import importlib.util
    import io
    import json
    from pathlib import Path
    from unittest.mock import MagicMock

    path = Path(__file__).resolve().parents[1] / 'backend/functions/analyze/app.py'
    spec = importlib.util.spec_from_file_location('local_analyze_handler', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    s3 = MagicMock()
    s3.get_object.return_value = {'Body': io.BytesIO(b'local-fixture')}
    with patch.object(module, 'get_s3_client', return_value=s3), patch('common.nova.boto3.client') as aws:
        response = module.lambda_handler({'body': json.dumps({'s3_key': 'uploads/test.jpg'})}, None)
        aws.assert_not_called()
    assert response['statusCode'] == 200
    analysis = json.loads(response['body'])['analysis']
    assert analysis['mock'] is True
    assert analysis['source'] == 'local_mock'
    assert 'no image inference' in analysis['description']


def test_evaluation_refuses_mock_metrics(local_mocks):
    from eval.rdd2022_eval import main
    with pytest.raises(ValueError, match='real inference'):
        main()
