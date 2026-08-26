"""Build and run the linear LangGraph executive report pipeline."""

import argparse
import logging
from datetime import date, datetime
from typing import cast

from langgraph.graph import END, START, StateGraph

from reports.metrics import retrieve_metrics
from reports.models import ReportState
from reports.publishing import publish_report
from reports.rendering import render_html
from reports.summary import summarize_metrics

logger = logging.getLogger(__name__)


def build_report_graph():
    """Compile the four-stage executive report graph."""

    builder = StateGraph(ReportState)
    builder.add_node("retrieve_metrics", retrieve_metrics)
    builder.add_node("summarize_metrics", summarize_metrics)
    builder.add_node("render_html", render_html)
    builder.add_node("publish_report", publish_report)

    builder.add_edge(START, "retrieve_metrics")
    builder.add_edge("retrieve_metrics", "summarize_metrics")
    builder.add_edge("summarize_metrics", "render_html")
    builder.add_edge("render_html", "publish_report")
    builder.add_edge("publish_report", END)
    return builder.compile()


REPORT_GRAPH = build_report_graph()


def normalize_report_date(value: str | date) -> date:
    """Validate external date input before it enters the graph."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def run_report(report_date: str | date) -> ReportState:
    """Run the complete report pipeline for any requested date."""

    normalized_date = normalize_report_date(report_date)
    logger.info("Starting executive report pipeline for %s", normalized_date)
    result = REPORT_GRAPH.invoke({"report_date": normalized_date})
    logger.info(
        "Completed executive report pipeline for %s: s3://%s/%s",
        normalized_date,
        result["published_bucket"],
        result["object_key"],
    )
    return cast(ReportState, result)


def main() -> None:
    """Run one report independently from the Airflow schedule."""

    parser = argparse.ArgumentParser(description="Build an UrbanGreen executive report")
    parser.add_argument("--date", required=True, help="report date in YYYY-MM-DD format")
    arguments = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = run_report(arguments.date)
    print(f"s3://{result['published_bucket']}/{result['object_key']}")


if __name__ == "__main__":
    main()
