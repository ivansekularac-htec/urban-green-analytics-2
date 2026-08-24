"""Daily executive report pipeline.

A small LangGraph graph that assembles the executive report end to end for a
given date: read the day's KPIs from the warehouse, have the local model write a
short narrative, render a self-contained HTML document, store it in the staging
bucket, and email the same document.

The graph is built from a `ReportDeps` bundle rather than reaching for its own
clients, so it runs the same whether the DAG builds those from the seeded
Airflow connections or `run.py` builds them from the environment.
"""
