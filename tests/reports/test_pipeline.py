"""Tests for LangGraph construction, ordering, and report-date input."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

from reports import pipeline

REPORT_DATE = date(2026, 8, 15)


def test_graph_contains_exactly_the_four_report_stages():
    nodes = set(pipeline.build_report_graph().get_graph().nodes)

    assert nodes == {
        "__start__",
        "retrieve_metrics",
        "summarize_metrics",
        "render_html",
        "publish_report",
        "__end__",
    }


def test_graph_executes_stages_in_order():
    calls = []

    def retrieve(state):
        calls.append("retrieve")
        return {"metrics": {}, "top_farms": []}

    def summarize(state):
        calls.append("summarize")
        return {"summary": MagicMock()}

    def render(state):
        calls.append("render")
        return {"html": "<html></html>"}

    def publish(state):
        calls.append("publish")
        return {"published_bucket": "staging", "object_key": "report.html"}

    with (
        patch("reports.pipeline.retrieve_metrics", retrieve),
        patch("reports.pipeline.summarize_metrics", summarize),
        patch("reports.pipeline.render_html", render),
        patch("reports.pipeline.publish_report", publish),
    ):
        graph = pipeline.build_report_graph()
        result = graph.invoke({"report_date": REPORT_DATE})

    assert calls == ["retrieve", "summarize", "render", "publish"]
    assert result["report_date"] == REPORT_DATE
    assert result["object_key"] == "report.html"


def test_external_date_input_is_normalized_once():
    assert pipeline.normalize_report_date("2026-08-15") == REPORT_DATE
    assert pipeline.normalize_report_date(REPORT_DATE) is REPORT_DATE
    assert pipeline.normalize_report_date(datetime(2026, 8, 15, 6, 0)) == REPORT_DATE


def test_run_report_passes_normalized_date_to_the_graph():
    final_state = {
        "report_date": REPORT_DATE,
        "published_bucket": "staging",
        "object_key": "reports/executive/date=2026-08-15/report.html",
    }

    with patch.object(pipeline.REPORT_GRAPH, "invoke", return_value=final_state) as invoke:
        result = pipeline.run_report("2026-08-15")

    invoke.assert_called_once_with({"report_date": REPORT_DATE})
    assert result == final_state
