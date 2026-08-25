"""Tests for Ollama executive report summarization."""

import json
from unittest import TestCase
from unittest.mock import MagicMock, patch
from urllib.error import URLError

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

    def test_summarize_metrics_uses_fallback_for_incomplete_response(self):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"message": {"content": json.dumps({"narrative": "", "insights": []})}}
        ).encode("utf-8")

        response.__enter__.return_value = response

        state = {
            "report_date": "2026-08-20",
            "metrics": {
                "reporting_farms": 75,
                "total_harvest_yield_kg": 1200.0,
                "total_energy_kwh": 2400.0,
                "energy_efficiency_kwh_per_kg": 2.0,
                "waste_reduction_progress": 0.10,
                "environmental_compliance_rate": 0.95,
                "sensor_anomaly_rate": 0.01,
                "total_sensor_readings": 18000,
            },
            "top_farms": [],
            "sensors": [],
        }

        with patch("report.summary.urlopen", return_value=response):
            result = summarize_metrics(state)

        self.assertIn("75 farms", result["narrative"])
        self.assertIn("95.0%", result["narrative"])
        self.assertEqual(len(result["insights"]), 2)


def test_summarize_metrics_uses_fallback_when_ollama_is_unavailable(self):
    state = {
        "report_date": "2026-08-20",
        "metrics": {
            "reporting_farms": 75,
            "total_harvest_yield_kg": 1200.0,
            "total_energy_kwh": 2400.0,
            "energy_efficiency_kwh_per_kg": 2.0,
            "waste_reduction_progress": 0.10,
            "environmental_compliance_rate": 0.95,
            "sensor_anomaly_rate": 0.01,
            "total_sensor_readings": 18000,
        },
        "top_farms": [],
        "sensors": [],
    }

    with patch(
        "report.summary.urlopen",
        side_effect=URLError("Ollama unavailable"),
    ):
        result = summarize_metrics(state)

    self.assertIn("75 farms", result["narrative"])
    self.assertIn("1.0%", result["narrative"])
    self.assertEqual(len(result["insights"]), 2)
