"""Linear LangGraph wiring for the daily executive report."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from reports.publish import publish
from reports.render import render_html
from reports.retrieve import retrieve_metrics
from reports.state import ReportState
from reports.summarize import summarize


def build_graph():
    graph = StateGraph(ReportState)
    graph.add_node("retrieve_metrics", retrieve_metrics)
    graph.add_node("summarize", summarize)
    graph.add_node("render_html", render_html)
    graph.add_node("publish", publish)
    graph.add_edge(START, "retrieve_metrics")
    graph.add_edge("retrieve_metrics", "summarize")
    graph.add_edge("summarize", "render_html")
    graph.add_edge("render_html", "publish")
    graph.add_edge("publish", END)
    return graph.compile()


REPORT_GRAPH = build_graph()


def run_report(report_date: str) -> ReportState:
    """Run the pipeline for any YYYY-MM-DD. Re-running overwrites the same object."""
    return REPORT_GRAPH.invoke({"report_date": report_date})
