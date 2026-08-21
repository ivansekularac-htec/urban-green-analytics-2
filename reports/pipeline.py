"""LangGraph pipeline for the UrbanGreen daily executive report."""

import logging
from datetime import date
from typing import cast

from langgraph.graph import END, START, StateGraph

from reports.email import send_report_email
from reports.metrics import retrieve_metrics
from reports.models import ReportState
from reports.output import publish_report, render_html
from reports.summary import summarize_metrics

logger = logging.getLogger(__name__)


def build_report_graph():
    """Build and compile the linear executive report graph."""
    builder = StateGraph(ReportState)

    builder.add_node("retrieve_metrics", retrieve_metrics)
    builder.add_node("summarize_metrics", summarize_metrics)
    builder.add_node("render_html", render_html)
    builder.add_node("publish_report", publish_report)
    builder.add_node("send_email", send_report_email)

    builder.add_edge(START, "retrieve_metrics")
    builder.add_edge("retrieve_metrics", "summarize_metrics")
    builder.add_edge("summarize_metrics", "render_html")
    builder.add_edge("render_html", "publish_report")
    builder.add_edge("publish_report", "send_email")
    builder.add_edge("send_email", END)

    return builder.compile()


REPORT_GRAPH = build_report_graph()


def run_report(report_date: str | date) -> ReportState:
    """Run the report pipeline for one reporting date."""
    if isinstance(report_date, date):
        normalized_date = report_date.isoformat()
    else:
        normalized_date = date.fromisoformat(report_date).isoformat()

    logger.info(f"Starting executive report for {normalized_date}")

    result = REPORT_GRAPH.invoke({"report_date": normalized_date})

    logger.info(f"Executive report completed for {normalized_date}")

    return cast(ReportState, result)
