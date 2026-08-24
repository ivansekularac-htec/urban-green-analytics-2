"""Tests for the HTML render node.

The report must be a self-contained document and must escape everything it
inserts, since the model's text reaches the page through here.
"""

from report.nodes.render import render_html
from report.nodes.summarize import SOURCE_FALLBACK, SOURCE_MODEL


def _state(kpis, **over):
    base = {
        "kpis": kpis,
        "narrative": "All nominal.",
        "insights": ["one", "two"],
        "summary_source": SOURCE_MODEL,
    }
    base.update(over)
    return base


def test_report_is_a_self_contained_document(sample_kpis):
    html = render_html(_state(sample_kpis))

    assert html.startswith("<!DOCTYPE html>")
    assert "<style>" in html
    # No external assets: nothing is fetched over the network.
    assert "http://" not in html
    assert "https://" not in html
    assert "<script" not in html


def test_the_figures_and_narrative_reach_the_page(sample_kpis):
    html = render_html(_state(sample_kpis))
    assert "75" in html  # active farms
    assert "All nominal." in html
    assert "UG Farm 043" in html


def test_injected_text_is_escaped(sample_kpis):
    html = render_html(_state(sample_kpis, narrative="<script>alert('x')</script>"))

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_a_malicious_farm_name_is_escaped(sample_kpis):
    sample_kpis["top_farms"][0]["farm"] = "<b>evil</b>"
    html = render_html(_state(sample_kpis))

    assert "<b>evil</b>" not in html
    assert "&lt;b&gt;evil" in html


def test_the_footer_states_who_wrote_the_narrative(sample_kpis):
    model_html = render_html(_state(sample_kpis, summary_source=SOURCE_MODEL))
    fallback_html = render_html(_state(sample_kpis, summary_source=SOURCE_FALLBACK))

    assert "written by the local model" in model_html
    assert "fallback" in fallback_html


def test_missing_figures_render_a_dash_not_a_crash():
    empty = {
        "report_date": "2026-01-01",
        "has_data": False,
        "totals": {},
        "active_farms": None,
        "top_farms": [],
    }
    html = render_html(_state(empty, narrative="No data."))

    assert "—" in html
    assert "No leaderboard rows" in html
