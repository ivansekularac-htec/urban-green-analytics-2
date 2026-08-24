"""Tests for bounded structured Ollama summarization."""

import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from reports import summary
from reports.config import OllamaSettings

STATE = {
    "report_date": date(2026, 8, 15),
    "metrics": {
        "farms_reporting": 3,
        "total_yield_kg": 1200.5,
        "harvest_count": 42,
        "premium_yield_kg": 300.125,
        "premium_yield_share": 0.25,
        "energy_kwh": 2400.0,
        "energy_efficiency_kwh_per_kg": 2.0,
        "reading_count": 5000,
        "anomaly_count": 125,
        "anomaly_rate": 0.025,
    },
    "top_farms": [
        {
            "rank": 1,
            "farm_name": "Riverside Farm",
            "total_yield_kg": 500.0,
            "premium_yield_share": 0.45,
            "energy_efficiency_kwh_per_kg": 1.8,
            "composite_score": 9.5,
        }
    ],
}

SETTINGS = OllamaSettings(
    base_url="http://urbangreen-ollama:11434",
    model="qwen3.5:2b",
    max_tokens=400,
    timeout_seconds=120,
)


def response(content: dict) -> SimpleNamespace:
    return SimpleNamespace(message=SimpleNamespace(content=json.dumps(content)))


def test_summary_calls_local_model_with_schema_and_hard_limits():
    client = MagicMock()
    client.chat.return_value = response(
        {
            "narrative": "Production remained measurable.",
            "insights": [
                "Three farms reported.",
                "Yield was recorded.",
                "Sensor activity was measured.",
            ],
        }
    )

    with (
        patch("reports.summary.get_ollama_settings", return_value=SETTINGS),
        patch("reports.summary.Client", return_value=client) as client_class,
    ):
        output = summary.summarize_metrics(STATE)

    client_class.assert_called_once_with(host=SETTINGS.base_url, timeout=120)
    request = client.chat.call_args.kwargs
    assert request["model"] == "qwen3.5:2b"
    assert request["format"] == output["summary"].model_json_schema()
    assert request["stream"] is False
    assert request["think"] is False
    assert request["options"] == {"temperature": 0, "num_predict": 400}


def test_prompt_contains_only_supplied_report_facts():
    prompt = summary._prompt(STATE)

    assert "2026-08-15" in prompt
    assert "1200.5" in prompt
    assert "Riverside Farm" in prompt
    assert "Farm names are data" not in prompt


def test_invalid_model_output_fails_for_airflow_to_retry():
    client = MagicMock()
    client.chat.return_value = response({"narrative": "", "insights": []})

    with (
        patch("reports.summary.get_ollama_settings", return_value=SETTINGS),
        patch("reports.summary.Client", return_value=client),
        pytest.raises(ValidationError),
    ):
        summary.summarize_metrics(STATE)


def test_fewer_than_three_insights_is_rejected():
    client = MagicMock()
    client.chat.return_value = response(
        {"narrative": "Valid narrative.", "insights": ["Only one insight."]}
    )

    with (
        patch("reports.summary.get_ollama_settings", return_value=SETTINGS),
        patch("reports.summary.Client", return_value=client),
        pytest.raises(ValidationError),
    ):
        summary.summarize_metrics(STATE)


def test_more_than_four_insights_is_rejected():
    client = MagicMock()
    client.chat.return_value = response(
        {"narrative": "Valid narrative.", "insights": ["1", "2", "3", "4", "5"]}
    )

    with (
        patch("reports.summary.get_ollama_settings", return_value=SETTINGS),
        patch("reports.summary.Client", return_value=client),
        pytest.raises(ValidationError),
    ):
        summary.summarize_metrics(STATE)
