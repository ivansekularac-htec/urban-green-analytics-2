"""LangGraph pipeline for the daily executive report."""

import argparse
from datetime import date

from langgraph.graph import END, START, StateGraph

from report.metrics import retrieve_metrics
from report.publish import publish_report
from report.render import render_html
from report.state import ReportState
from report.summary import summarize_metrics


def _build_graph():
    """Build the linear executive report graph."""
    graph = StateGraph(ReportState)

    graph.add_node("retrieve_metrics", retrieve_metrics)
    graph.add_node("summarize_metrics", summarize_metrics)
    graph.add_node("render_html", render_html)
    graph.add_node("publish_report", publish_report)

    graph.add_edge(START, "retrieve_metrics")
    graph.add_edge("retrieve_metrics", "summarize_metrics")
    graph.add_edge("summarize_metrics", "render_html")
    graph.add_edge("render_html", "publish_report")
    graph.add_edge("publish_report", END)

    return graph.compile()


REPORT_GRAPH = _build_graph()


def run_report(report_date: str) -> str:
    """Run the report pipeline and return the published object key."""
    date.fromisoformat(report_date)

    result = REPORT_GRAPH.invoke({"report_date": report_date})

    return result["object_key"]


def main() -> None:
    """Run the executive report pipeline from the command line."""
    parser = argparse.ArgumentParser(
        description="Generate an UrbanGreen executive report."
    )

    parser.add_argument(
        "--date",
        required=True,
        help="Report date in YYYY-MM-DD format.",
    )

    args = parser.parse_args()

    object_key = run_report(args.date)

    print(object_key)


if __name__ == "__main__":
    main()
