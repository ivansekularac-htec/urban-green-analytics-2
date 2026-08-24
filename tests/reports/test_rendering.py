"""Tests for self-contained and safely escaped HTML rendering."""

import re
from datetime import date

from reports.models import ReportSummary
from reports.rendering import render_html


def report_state():
    return {
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
        "summary": ReportSummary(
            narrative="UrbanGreen recorded a measurable production day.",
            insights=[
                "Three farms reported data.",
                "The anomaly rate was 2.50%.",
                "Energy consumption was measured.",
            ],
        ),
    }


def test_template_contains_date_kpis_narrative_and_leaderboard():
    html = render_html(report_state())["html"]

    assert html.startswith("<!doctype html>")
    assert "2026-08-15" in html
    assert "1,200.50" in html
    assert "UrbanGreen recorded a measurable production day." in html
    assert "Three farms reported data." in html
    assert "Riverside Farm" in html


def test_html_is_self_contained():
    html = render_html(report_state())["html"]

    assert "http://" not in html
    assert "https://" not in html
    assert "<link" not in html
    assert "@import" not in html
    assert not re.search(r"<(img|script)\b", html)


def test_warehouse_and_model_text_is_escaped():
    state = report_state()
    state["top_farms"][0]["farm_name"] = "<script>alert(1)</script>"
    state["summary"] = ReportSummary(
        narrative="<img src=x onerror=alert(1)>",
        insights=["<b>unsafe</b>", "Safe insight.", "Another safe insight."],
    )

    html = render_html(state)["html"]

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<img src=x" not in html
    assert "&lt;img" in html


def test_unavailable_ratios_are_not_presented_as_zero():
    state = report_state()
    state["metrics"]["premium_yield_share"] = None
    state["metrics"]["energy_efficiency_kwh_per_kg"] = None
    state["metrics"]["anomaly_rate"] = None

    html = render_html(state)["html"]

    assert html.count("Not measured") >= 3


def test_same_input_renders_deterministically():
    state = report_state()
    assert render_html(state)["html"] == render_html(state)["html"]
