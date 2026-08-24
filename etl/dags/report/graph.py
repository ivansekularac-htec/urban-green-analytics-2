"""The linear report graph: retrieve, summarize, render, store, email.

The stages run in order, each adding its keys to the state. The graph is built
from a `ReportDeps` so the same shape runs in the DAG, from `run.py`, and in a
test - only the dependencies differ.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from report.deps import ReportDeps
from report.nodes.email import make_email
from report.nodes.render import make_render
from report.nodes.retrieve import make_retrieve
from report.nodes.store import make_store
from report.nodes.summarize import make_summarize
from report.state import ReportState


def build_graph(deps: ReportDeps):
    """Compile the linear report graph against a set of dependencies."""
    graph = StateGraph(ReportState)

    graph.add_node("retrieve", make_retrieve(deps))
    graph.add_node("summarize", make_summarize(deps))
    graph.add_node("render", make_render(deps))
    graph.add_node("store", make_store(deps))
    graph.add_node("email", make_email(deps))

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "summarize")
    graph.add_edge("summarize", "render")
    graph.add_edge("render", "store")
    graph.add_edge("store", "email")
    graph.add_edge("email", END)

    return graph.compile()


def run_report(deps: ReportDeps, report_date: str) -> ReportState:
    """Run the whole pipeline for one date and return the final state.

    The state carries `object_key` (where the report was stored),
    `summary_source` (model or fallback), and `email_sent`.
    """
    graph = build_graph(deps)
    return graph.invoke({"report_date": report_date})
