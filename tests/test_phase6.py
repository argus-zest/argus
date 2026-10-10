import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure layer is importable
sys.path.insert(0, os.path.abspath("backend/layer/python"))
import backtest.run_backtest as run_backtest
import eval.rdd2022_eval as rdd2022_eval


class TestPhase6Evidence(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = os.path.abspath("tests/fixtures")
        os.makedirs(self.fixtures_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.fixtures_dir):
            shutil.rmtree(self.fixtures_dir, ignore_errors=True)

    def test_rdd2022_eval_missing_input_exits_zero(self):
        # Run script with non-existent data directory
        cmd = [sys.executable, "eval/rdd2022_eval.py", "--data-dir", "tests/fixtures/non_existent"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Missing input must exit 0: {res.stderr}")
        self.assertIn("missing or empty", res.stdout)

    def test_backtest_missing_input_exits_zero(self):
        # Run script with default placeholder events.json
        cmd = [sys.executable, "backtest/run_backtest.py", "--events", "backtest/events.json"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Missing real events must exit 0: {res.stderr}")
        self.assertIn("No real events configured", res.stdout)

    @patch("common.nova.converse")
    def test_rdd2022_eval_on_fixtures(self, mock_converse):
        # Mock Nova Converse response
        mock_converse.return_value = {
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
                                    "confidence": 0.9,
                                    "description": "Pothole detected",
                                    "visible_evidence": "Dark road hole",
                                },
                            }
                        }
                    ]
                }
            }
        }

        # Setup 4 fake images + Pascal VOC XMLs
        rdd_fixture_dir = os.path.join(self.fixtures_dir, "rdd2022")
        img_dir = os.path.join(rdd_fixture_dir, "images")
        xml_dir = os.path.join(rdd_fixture_dir, "annotations", "xmls")
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(xml_dir, exist_ok=True)

        # 2 positives with D40, 2 negatives without D00/D10/D20/D40
        for i, is_pos in enumerate([True, True, False, False]):
            name = f"img_{i}"
            # Create tiny JPEG image
            with open(os.path.join(img_dir, f"{name}.jpg"), "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00")

            tag = "D40" if is_pos else "other"
            xml_content = f"<annotation><object><name>{tag}</name></object></annotation>"
            with open(os.path.join(xml_dir, f"{name}.xml"), "w") as f:
                f.write(xml_content)

        out_dir = os.path.join(self.fixtures_dir, "results")
        test_args = ["rdd2022_eval.py", "--data-dir", rdd_fixture_dir, "--out-dir", out_dir]

        with patch.object(sys, "argv", test_args):
            rdd2022_eval.main()

        res_path = os.path.join(out_dir, "rdd2022.json")
        self.assertTrue(os.path.exists(res_path), "rdd2022.json must be generated")
        with open(res_path, "r", encoding="utf-8") as f:
            res = json.load(f)

        self.assertEqual(res["dataset"], "RDD2022 India")
        self.assertEqual(res["level"], "image")
        self.assertEqual(res["n_pos"], 2)
        self.assertEqual(res["n_neg"], 2)
        self.assertIn("precision", res)
        self.assertIn("recall", res)
        self.assertIn("f1", res)

    @patch("backtest.run_backtest.fetch_event_rainfall")
    def test_backtest_on_fixtures(self, mock_rain):
        # Mock rainfall for 3 fake events: rain_3h = 45.0, rain_prev24h = 30.0
        mock_rain.return_value = (45.0, 30.0)

        events_data = [
            {
                "event_id": "EVT-TEST-01",
                "date": "2024-07-10",
                "description": "Heavy monsoon rainfall day 1",
                "held_out": False,
                "reported_hotspot_ids": ["minto_bridge", "tilak_bridge"],
                "reported_other_count": 2,
                "source_urls": ["https://example.com/delhi-rain-1"],
                "status": "ACTIVE",
            },
            {
                "event_id": "EVT-TEST-02",
                "date": "2024-08-01",
                "description": "Severe cloudburst event",
                "held_out": True,
                "reported_hotspot_ids": ["zakhira_underpass"],
                "reported_other_count": 1,
                "source_urls": ["https://example.com/delhi-rain-2"],
                "status": "ACTIVE",
            },
            {
                "event_id": "EVT-TEST-03",
                "date": "2024-08-20",
                "description": "Moderate localized waterlogging",
                "held_out": True,
                "reported_hotspot_ids": ["moolchand"],
                "reported_other_count": 0,
                "source_urls": ["https://example.com/delhi-rain-3"],
                "status": "ACTIVE",
            },
        ]

        events_file = os.path.join(self.fixtures_dir, "test_events.json")
        with open(events_file, "w", encoding="utf-8") as f:
            json.dump(events_data, f)

        out_dir = os.path.join(self.fixtures_dir, "backtest_results")
        test_args = ["run_backtest.py", "--events", events_file, "--out-dir", out_dir]

        with patch.object(sys, "argv", test_args):
            run_backtest.main()

        res_path = os.path.join(out_dir, "backtest.json")
        self.assertTrue(os.path.exists(res_path), "backtest.json must be generated")
        with open(res_path, "r", encoding="utf-8") as f:
            res = json.load(f)

        self.assertEqual(len(res["events"]), 3)
        ev0 = res["events"][0]
        self.assertEqual(ev0["event_id"], "EVT-TEST-01")
        self.assertIn("precision_at_20", ev0)
        self.assertIn("recall", ev0)
        self.assertIn("random_baseline_precision", ev0)
        self.assertIn("top_20", ev0)
        self.assertTrue(len(ev0["top_20"]) > 0)


if __name__ == "__main__":
    unittest.main()
