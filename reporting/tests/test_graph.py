"""Tests for the pipeline graph.

The stages are tested in their own modules. What is asserted here is the
wiring: that the four run in order and that each one is handed what the
previous one produced.
"""

from datetime import date
from unittest.mock import patch

from app import graph

DAY = date(2026, 8, 15)

METRICS = {"day": DAY, "totals": {"farms": 75}}
SUMMARY = {"narrative": "Yield held steady.", "insights": [], "source": "qwen3.5:2b"}
PUBLISHED = {"key": "reports/executive/date=2026-08-15/report.html", "warnings": []}


def run_with_stubs():
    """Run the pipeline with every stage stubbed, returning the state and mocks."""

    with (
        patch("app.graph.metrics") as metrics,
        patch("app.graph.llm") as llm,
        patch("app.graph.report") as report,
        patch("app.graph.publish") as publish,
    ):
        metrics.collect.return_value = METRICS
        llm.summarize.return_value = SUMMARY
        report.render.return_value = "<html>report</html>"
        publish.publish.return_value = PUBLISHED

        state = graph.run(DAY)

    return state, metrics, llm, report, publish


def test_the_graph_has_the_four_stages():
    nodes = graph.build_graph().get_graph().nodes

    assert {"fetch_metrics", "summarize", "render", "publish"} <= set(nodes)


def test_each_stage_is_handed_what_the_previous_one_produced():
    state, metrics, llm, report, publish = run_with_stubs()

    metrics.collect.assert_called_once_with(metrics.get_client.return_value, DAY)
    llm.summarize.assert_called_once_with(METRICS)
    report.render.assert_called_once_with(METRICS, SUMMARY)
    publish.publish.assert_called_once_with("<html>report</html>", DAY)

    assert state["published"] == PUBLISHED


def test_the_finished_state_carries_every_stage_result():
    state, *_ = run_with_stubs()

    assert state["day"] == DAY
    assert state["metrics"] == METRICS
    assert state["summary"] == SUMMARY
    assert state["html"] == "<html>report</html>"


def test_a_fallback_summary_still_reaches_the_report():
    # llm.summarize falls back rather than raising, so the pipeline must carry
    # the fallback through instead of stopping.
    fallback = {"narrative": "75 farms recorded.", "insights": [], "source": "fallback"}

    with (
        patch("app.graph.metrics") as metrics,
        patch("app.graph.llm") as llm,
        patch("app.graph.report") as report,
        patch("app.graph.publish") as publish,
    ):
        metrics.collect.return_value = METRICS
        llm.summarize.return_value = fallback
        report.render.return_value = "<html>report</html>"
        publish.publish.return_value = PUBLISHED

        state = graph.run(DAY)

    report.render.assert_called_once_with(METRICS, fallback)
    assert state["published"] == PUBLISHED
