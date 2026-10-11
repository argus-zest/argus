"""Exercise actual SDK signing locally with dummy credentials; no AWS requests."""
import json
from urllib.parse import parse_qs, urlparse

from backend.functions.presign import app as uploads
from backend.functions.cases import app as cases
from backend.functions.sfn_notice_agent import app as notices


def test_upload_and_evidence_links_use_sydney_signature_v4(monkeypatch):
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_REGION', 'ap-southeast-2')
    monkeypatch.setenv('BUCKET', 'argus-262952461520-ap-southeast-2')
    response = uploads.lambda_handler({'body': json.dumps({
        'purpose': 'report', 'content_type': 'image/jpeg',
    })}, None)
    assert response['statusCode'] == 200
    urls = [json.loads(response['body'])['upload_url']]
    for make_client in [cases.get_s3, notices.get_s3]:
        urls.append(make_client().generate_presigned_url('get_object', Params={
            'Bucket': 'argus-262952461520-ap-southeast-2', 'Key': 'uploads/test.jpg',
        }, ExpiresIn=300))
    for url in urls:
        parsed = urlparse(url)
        assert parsed.hostname == 'argus-262952461520-ap-southeast-2.s3.ap-southeast-2.amazonaws.com'
        query = parse_qs(parsed.query)
        assert query['X-Amz-Algorithm'] == ['AWS4-HMAC-SHA256']
        assert '/ap-southeast-2/s3/aws4_request' in query['X-Amz-Credential'][0]
        assert 'AWSAccessKeyId' not in query
