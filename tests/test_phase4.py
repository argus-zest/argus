import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

# Ensure backend/layer/python and functions are in sys.path
sys.path.insert(0, os.path.abspath("backend/layer/python"))
sys.path.insert(0, os.path.abspath("backend/functions/presign"))
sys.path.insert(0, os.path.abspath("backend/functions/analyze"))
sys.path.insert(0, os.path.abspath("backend/functions/tender_clause"))

from common.nova import (
    converse,
    analyze_hazard,
    verify_fix,
    extract_clause,
    NovaError,
)
import app as presign_app
from importlib import import_module


class TestPhase4NovaAndWriteAPIs(unittest.TestCase):
    def setUp(self):
        os.environ["AWS_REGION"] = "ap-southeast-2"
        os.environ["NOVA_MODEL_ID"] = "amazon.nova-lite-v1:0"
        os.environ["BUCKET"] = "test-bucket"

    @patch("common.nova.get_bedrock_client")
    def test_forced_tool_parsing(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Bedrock Converse toolUse response
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool_123",
                                "name": "report_hazard",
                                "input": {
                                    "hazard_type": "open_manhole",
                                    "severity": 4,
                                    "submerged": True,
                                    "confidence": 0.85,
                                    "description": "Dangerous open manhole submerged in water",
                                    "visible_evidence": "Circular opening with churning water",
                                },
                            }
                        }
                    ]
                }
            }
        }

        fake_img = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        res = analyze_hazard(fake_img, "jpeg")

        self.assertEqual(res["hazard_type"], "open_manhole")
        self.assertEqual(res["severity"], 4)
        self.assertTrue(res["submerged"])
        self.assertEqual(res["confidence"], 0.85)
        self.assertEqual(res["description"], "Dangerous open manhole submerged in water")

    @patch("common.nova.get_bedrock_client")
    def test_json_text_fallback(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Bedrock response without toolUse, but with json text
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps({
                                "hazard_type": "pothole",
                                "severity": 3,
                                "submerged": False,
                                "confidence": 0.72,
                                "description": "Medium pothole near curb",
                                "visible_evidence": "Broken pavement edges",
                            })
                        }
                    ]
                }
            }
        }

        fake_img = b"\xff\xd8\xff\xe0" + b"\x00" * 50
        res = analyze_hazard(fake_img, "jpeg")

        self.assertEqual(res["hazard_type"], "pothole")
        self.assertEqual(res["severity"], 3)
        self.assertFalse(res["submerged"])
        self.assertEqual(res["confidence"], 0.72)

    @patch("common.nova.get_bedrock_client")
    def test_model_region_error_does_not_retry_cross_region(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        err_response = {"Error": {"Code": "ValidationException", "Message": "Model not supported in region"}}
        mock_client.converse.side_effect = ClientError(err_response, "Converse")

        with self.assertRaises(NovaError) as ctx:
            converse(
                messages=[{"role": "user", "content": [{"text": "test"}]}],
                system="test",
            )

        self.assertEqual(ctx.exception.code, "ValidationException")
        self.assertEqual(mock_client.converse.call_count, 1)
        self.assertEqual(mock_client.converse.call_args.kwargs["modelId"], "amazon.nova-lite-v1:0")

    @patch("common.nova.get_bedrock_client")
    def test_cross_region_model_override_is_rejected(self, mock_get_client):
        os.environ["NOVA_MODEL_ID"] = "global.amazon.nova-2-lite-v1:0"
        with self.assertRaises(NovaError) as ctx:
            converse(
                messages=[{"role": "user", "content": [{"text": "test"}]}],
                system="test",
            )
        self.assertEqual(ctx.exception.code, "REGION_POLICY")
        mock_get_client.assert_not_called()

    def test_image_too_large_rejection(self):
        # 3.6 MB image
        huge_img = b"0" * int(3.6 * 1024 * 1024)
        with self.assertRaises(NovaError) as ctx:
            analyze_hazard(huge_img, "jpeg")
        self.assertEqual(ctx.exception.code, "IMAGE_TOO_LARGE")

    @patch("common.nova.get_bedrock_client")
    def test_verify_fix_without_before_bytes(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "name": "report_verification",
                                "input": {
                                    "hazard_still_present": False,
                                    "same_location_plausible": True,
                                    "confidence": 0.88,
                                    "explanation": "Clear fresh asphalt surface",
                                },
                            }
                        }
                    ]
                }
            }
        }

        after_img = b"\xff\xd8" + b"\x00" * 50
        res = verify_fix(before_bytes=None, after_bytes=after_img, hazard_type="pothole")

        self.assertFalse(res["hazard_still_present"])
        self.assertIsNone(res["same_location_plausible"])  # must be null when before_bytes is None
        self.assertEqual(res["confidence"], 0.88)

    @patch("common.nova.get_bedrock_client")
    def test_extract_clause(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "name": "report_clause",
                                "input": {
                                    "found": True,
                                    "quote": "Clause 17: Defect liability is 5 years.",
                                    "page_hint": "Page 12",
                                },
                            }
                        }
                    ]
                }
            }
        }

        fake_pdf = b"%PDF-1.4" + b"\x00" * 100
        res = extract_clause(fake_pdf, "pwd_tender_2023.pdf")

        self.assertTrue(res["found"])
        self.assertIn("Clause 17", res["quote"])
        self.assertEqual(res["page_hint"], "Page 12")
        self.assertTrue(res["verified_in_text"])

    @patch("backend.functions.presign.app.get_s3_client")
    def test_presign_handler(self, mock_get_s3):
        mock_s3 = MagicMock()
        mock_get_s3.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/uploads/mock.jpg?signature"

        from backend.functions.presign.app import lambda_handler as presign_handler

        event = {
            "body": json.dumps({"purpose": "report", "content_type": "image/jpeg"}),
            "requestContext": {"http": {"method": "POST", "path": "/v1/uploads/presign"}},
        }
        resp = presign_handler(event, None)
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertIn("upload_url", body)
        self.assertIn("s3_key", body)
        self.assertTrue(body["s3_key"].startswith("uploads/"))
        self.assertTrue(body["s3_key"].endswith(".jpg"))

        # Bad content type
        event_bad = {
            "body": json.dumps({"purpose": "report", "content_type": "image/gif"}),
            "requestContext": {"http": {"method": "POST"}},
        }
        resp_bad = presign_handler(event_bad, None)
        self.assertEqual(resp_bad["statusCode"], 400)

    @patch("backend.functions.tender_clause.app.get_s3_client")
    @patch("common.nova.get_bedrock_client")
    def test_tender_clause_handler(self, mock_bedrock, mock_s3):
        mock_s3_client = MagicMock()
        mock_s3.return_value = mock_s3_client
        mock_s3_client.get_object.return_value = {"Body": MagicMock(read=lambda: b"%PDF-1.5 test")}

        mock_bedrock_client = MagicMock()
        mock_bedrock.return_value = mock_bedrock_client
        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "name": "report_clause",
                                "input": {
                                    "found": True,
                                    "quote": "Clause 5: Road warranty 3 years.",
                                    "page_hint": "Page 7",
                                },
                            }
                        }
                    ]
                }
            }
        }

        from backend.functions.tender_clause.app import lambda_handler as tender_handler

        # Bad doc_key not starting with tenders/
        bad_event = {"body": json.dumps({"doc_key": "other/doc.pdf"})}
        resp = tender_handler(bad_event, None)
        self.assertEqual(resp["statusCode"], 400)

        # Good doc_key
        good_event = {"body": json.dumps({"doc_key": "tenders/road_work.pdf"})}
        resp = tender_handler(good_event, None)
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertTrue(body["found"])
        self.assertEqual(body["quote"], "Clause 5: Road warranty 3 years.")

    @patch("backend.functions.analyze.app.get_s3_client")
    @patch("common.nova.get_bedrock_client")
    def test_analyze_handler(self, mock_bedrock, mock_s3):
        mock_s3_client = MagicMock()
        mock_s3.return_value = mock_s3_client
        mock_s3_client.get_object.return_value = {"Body": MagicMock(read=lambda: b"\xff\xd8\xff\xe0" + b"\x00" * 50)}

        mock_bedrock_client = MagicMock()
        mock_bedrock.return_value = mock_bedrock_client
        mock_bedrock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "name": "report_hazard",
                                "input": {
                                    "hazard_type": "pothole",
                                    "severity": 4,
                                    "submerged": False,
                                    "confidence": 0.91,
                                    "description": "Hazard tested",
                                    "visible_evidence": "Pothole tested",
                                },
                            }
                        }
                    ]
                }
            }
        }

        from backend.functions.analyze.app import lambda_handler as analyze_handler

        event = {"body": json.dumps({"s3_key": "uploads/pothole.jpg"})}
        resp = analyze_handler(event, None)
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["analysis"]["hazard_type"], "pothole")
        self.assertEqual(body["analysis"]["severity"], 4)


if __name__ == "__main__":
    unittest.main()

