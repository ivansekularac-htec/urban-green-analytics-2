"""The report pipeline as a linear LangGraph graph.

Each node wraps one stage. The work itself lives in the modules beside this
one, so this file is wiring and nothing else.
"""

from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app import llm, metrics, publish, report


class ReportState(TypedDict, total=False):
    day: date
    metrics: dict
    summary: dict
    html: str
    published: dict


def fetch_metrics(state: ReportState) -> ReportState:
    """Read the day's figures from the warehouse."""

    return {"metrics": metrics.collect(metrics.get_client(), state["day"])}


def summarize(state: ReportState) -> ReportState:
    """Have the local model write the narrative."""

    return {"summary": llm.summarize(state["metrics"])}


def render(state: ReportState) -> ReportState:
    """Render the report as one HTML document."""

    return {"html": report.render(state["metrics"], state["summary"])}


def publish_report(state: ReportState) -> ReportState:
    """Store the report in the bucket and email it."""

    return {"published": publish.publish(state["html"], state["day"])}


def build_graph():
    """Build and compile the pipeline."""

    graph = StateGraph(ReportState)

    graph.add_node("fetch_metrics", fetch_metrics)
    graph.add_node("summarize", summarize)
    graph.add_node("render", render)
    graph.add_node("publish", publish_report)

    graph.add_edge(START, "fetch_metrics")
    graph.add_edge("fetch_metrics", "summarize")
    graph.add_edge("summarize", "render")
    graph.add_edge("render", "publish")
    graph.add_edge("publish", END)

    return graph.compile()


def run(day: date) -> ReportState:
    """Run the pipeline for one day and return the finished state."""

    return build_graph().invoke({"day": day})
