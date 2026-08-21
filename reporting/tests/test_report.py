"""Tests for rendering the report."""

import re
from datetime import date

from app import report

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
        "anomaly_rate": 0.0011,
    },
    "sensors": [{"sensor_type": "Temperature", "unit": "C", "readings": 150, "anomalies": 1}],
    "leaderboard": [{"farm": "UG Farm 026", "yield_kg": 36.8, "premium_share": 0.51, "rank": 1}],
}

SUMMARY = {"narrative": "Yield held steady.", "insights": ["One", "Two"], "source": "qwen3.5:2b"}


def test_the_report_carries_the_days_figures():
    html = report.render(METRICS, SUMMARY)

    assert "2026-08-15" in html
    assert "1,892.3" in html
    assert "Yield held steady." in html
    assert "UG Farm 026" in html
    assert "Temperature" in html


def test_the_report_names_where_the_summary_came_from():
    assert "qwen3.5:2b" in report.render(METRICS, SUMMARY)
    assert "fallback" in report.render(METRICS, {**SUMMARY, "source": "fallback"})


def test_a_missing_measurement_is_not_shown_as_zero():
    metrics = {**METRICS, "totals": {**METRICS["totals"], "energy_per_kg": None}}

    html = report.render(metrics, SUMMARY)

    assert "not measured" in html


def test_untrusted_text_is_escaped():
    # Farm names are user input and the narrative is model output.
    metrics = {
        **METRICS,
        "leaderboard": [{**METRICS["leaderboard"][0], "farm": "<script>x</script>"}],
    }
    summary = {**SUMMARY, "narrative": "<img onerror=alert(1)>"}

    html = report.render(metrics, summary)

    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<img onerror" not in html


def test_the_document_is_self_contained():
    html = report.render(METRICS, SUMMARY)

    # Nothing to fetch: no remote stylesheet, script, image or font.
    assert "http://" not in html
    assert "https://" not in html
    assert "<link" not in html
    assert "@import" not in html
    assert not re.search(r"<(img|script)\b", html)


def test_empty_sections_are_left_out():
    metrics = {**METRICS, "sensors": [], "leaderboard": []}

    html = report.render(metrics, SUMMARY)

    assert "Top farms" not in html
    assert "Sensors" not in html
    assert "Key figures" in html


def test_the_number_filter_handles_missing_values():
    assert report.number(None) == "not measured"
    assert report.number(1892.3) == "1,892.3"
    assert report.number(1425) == "1,425"
    assert report.percent(None) == "not measured"
    assert report.percent(0.0011) == "0.11%"
