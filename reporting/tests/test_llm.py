"""Tests for the summarization stage."""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import httpx

from app import llm

METRICS = {
    "day": date(2026, 8, 15),
    "totals": {
        "farms": 75,
        "harvests": 1425,
        "yield_kg": 1892.3,
        "energy_kwh": 17039.1,
        "energy_per_kg": 9.0,
        "readings": 1760,
        "anomalies": 2,
        "anomaly_rate": 0.001,
    },
    "sensors": [],
    "leaderboard": [{"farm": "UG Farm 026", "yield_kg": 36.8, "rank": 1}],
}


def reply(narrative="Yield held steady.", insights=("One", "Two")) -> MagicMock:
    """Build an Ollama chat response carrying a JSON content payload."""

    response = MagicMock()
    response.json.return_value = {
        "message": {"content": json.dumps({"narrative": narrative, "insights": list(insights)})}
    }

    return response


def test_a_good_reply_becomes_the_narrative_and_insights():
    with patch("app.llm.httpx.post", return_value=reply()):
        summary = llm.summarize(METRICS)

    assert summary["narrative"] == "Yield held steady."
    assert summary["insights"] == ["One", "Two"]
    assert summary["source"] != "fallback"


def test_the_request_bounds_what_the_model_may_do():
    with patch("app.llm.httpx.post", return_value=reply()) as post:
        llm.summarize(METRICS)

    body = post.call_args.kwargs["json"]

    assert body["format"] == llm._SCHEMA
    assert body["think"] is False
    assert body["stream"] is False
    assert body["options"]["num_predict"] == llm.NUM_PREDICT
    assert post.call_args.kwargs["timeout"] == llm.TIMEOUT_SECONDS


def test_the_prompt_carries_the_figures_and_no_others():
    with patch("app.llm.httpx.post", return_value=reply()) as post:
        llm.summarize(METRICS)

    prompt = post.call_args.kwargs["json"]["messages"][0]["content"]

    assert "1892.3" in prompt
    assert "UG Farm 026" in prompt
    assert "do not invent" in prompt


def test_too_many_insights_are_cut_to_the_limit():
    many = tuple(f"insight {number}" for number in range(10))

    with patch("app.llm.httpx.post", return_value=reply(insights=many)):
        summary = llm.summarize(METRICS)

    assert len(summary["insights"]) == llm.MAX_INSIGHTS


def test_a_timeout_falls_back_instead_of_failing():
    with patch("app.llm.httpx.post", side_effect=httpx.TimeoutException("too slow")):
        summary = llm.summarize(METRICS)

    assert summary["source"] == "fallback"
    assert "1892.3 kg" in summary["narrative"]


def test_an_unparseable_reply_falls_back():
    response = MagicMock()
    response.json.return_value = {"message": {"content": "not json at all"}}

    with patch("app.llm.httpx.post", return_value=response):
        assert llm.summarize(METRICS)["source"] == "fallback"


def test_an_empty_narrative_falls_back():
    with patch("app.llm.httpx.post", return_value=reply(narrative="   ")):
        assert llm.summarize(METRICS)["source"] == "fallback"


def test_the_fallback_narrative_states_the_days_figures():
    summary = llm.fallback(METRICS)

    assert "75 farms" in summary["narrative"]
    assert "1425 harvests" in summary["narrative"]
    assert summary["insights"] == []
