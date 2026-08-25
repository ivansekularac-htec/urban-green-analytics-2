"""Tests for Ollama executive report summarization."""

import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from report.summary import (
    _summary_prompt,
    summarize_metrics,
)


class SummarizeMetricsTests(TestCase):
    def _ollama_response(self, summary):
        response = MagicMock()

        response.read.return_value = json.dumps(
            {"message": {"content": json.dumps(summary)}}
        ).encode("utf-8")

        context_manager = MagicMock()
        context_manager.__enter__.return_value = response

        return context_manager

    def test_summary_prompt_contains_report_context(self):
        prompt = _summary_prompt(
            "2026-08-20",
            {
                "reporting_farms": 75,
                "total_harvest_yield_kg": 1200.5,
                "sensor_anomaly_rate": 0.02,
            },
            [
                {
                    "rank": 1,
                    "farm": "UG Farm 01",
                    "city": "Cologne",
                    "total_yield_kg": 250.5,
                }
            ],
            [
                {
                    "sensor_type": "Temperature",
                    "unit": "°C",
                    "readings": 3000,
                    "anomalies": 30,
                    "anomaly_rate": 0.01,
                    "compliance_rate": 0.95,
                }
            ],
        )

        self.assertIn("2026-08-20", prompt)
        self.assertIn("total_harvest_yield_kg", prompt)
        self.assertIn("sensor_anomaly_rate", prompt)
        self.assertIn("UG Farm 01", prompt)
        self.assertIn("Temperature", prompt)
        self.assertIn("Do not infer why", prompt)
        self.assertIn("Do not describe reporting_farms as active farms", prompt)
        self.assertIn("describe it as unavailable rather than zero", prompt)

    def test_summarize_metrics_returns_structured_summary(self):
        ollama_response = self._ollama_response(
            {
                "narrative": (
                    "UrbanGreen reported 1,200.5 kg of harvest "
                    "yield across 75 reporting farms."
                ),
                "insights": [
                    "UG Farm 01 ranked first on the daily leaderboard.",
                    "Temperature readings had a 1.0% anomaly rate.",
                ],
            }
        )

        state = {
            "report_date": "2026-08-20",
            "metrics": {
                "reporting_farms": 75,
                "total_harvest_yield_kg": 1200.5,
                "sensor_anomaly_rate": 0.02,
            },
            "top_farms": [
                {
                    "rank": 1,
                    "farm": "UG Farm 01",
                    "city": "Cologne",
                    "total_yield_kg": 250.5,
                }
            ],
            "sensors": [
                {
                    "sensor_type": "Temperature",
                    "unit": "°C",
                    "readings": 3000,
                    "anomalies": 30,
                    "anomaly_rate": 0.01,
                    "compliance_rate": 0.95,
                }
            ],
        }

        with patch(
            "report.summary.urlopen",
            return_value=ollama_response,
        ) as urlopen:
            result = summarize_metrics(state)

        self.assertEqual(
            result,
            {
                "narrative": (
                    "UrbanGreen reported 1,200.5 kg of harvest "
                    "yield across 75 reporting farms."
                ),
                "insights": [
                    ("UG Farm 01 ranked first on the daily leaderboard."),
                    ("Temperature readings had a 1.0% anomaly rate."),
                ],
            },
        )

        request = urlopen.call_args.args[0]

        payload = json.loads(request.data.decode("utf-8"))

        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])

        self.assertEqual(
            payload["options"]["num_predict"],
            220,
        )

        self.assertEqual(
            payload["format"]["required"],
            ["narrative", "insights"],
        )

        prompt = payload["messages"][0]["content"]

        self.assertIn("UG Farm 01", prompt)
        self.assertIn("Temperature", prompt)

    def test_summarize_metrics_rejects_incomplete_response(self):
        ollama_response = self._ollama_response(
            {
                "narrative": "",
                "insights": ["Only one insight."],
            }
        )

        with patch(
            "report.summary.urlopen",
            return_value=ollama_response,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "incomplete executive summary",
            ):
                summarize_metrics(
                    {
                        "report_date": "2026-08-20",
                        "metrics": {"reporting_farms": 75},
                        "top_farms": [],
                        "sensors": [],
                    }
                )
