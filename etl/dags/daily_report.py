"""Airflow DAG for the daily executive report.

The pipeline itself is the LangGraph graph in the reporting service, so it can
be run and tested without a scheduler. This DAG supplies the schedule and the
report date, and records the object key the run published.
"""

import json
import logging
import os
import urllib.request
from datetime import datetime, timedelta

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import dag

logger = logging.getLogger(__name__)

REPORTING_URL = os.environ.get("REPORTING_URL", "http://urbangreen-reporting:8002")

# One request covers the warehouse queries, the inference and both publish
# sinks. Generous on purpose: the service has its own, shorter timeout on the
# model, so this bound should never be the one that trips.
REQUEST_TIMEOUT_SECONDS = 600

# app.llm marks the summary with the model that wrote it, or with this when it
# gave up and used the fixed narrative.
FALLBACK_SUMMARY_SOURCE = "fallback"


def build_report(day: str) -> str:
    """Ask the reporting service for one day's report.

    Args:
        day: Report date as YYYY-MM-DD.

    Returns:
        The object key the report was published under, which Airflow stores as
        the task result.

    Raises:
        RuntimeError: If the report was not stored, or was published with the
            fallback narrative instead of a model-written one.
    """

    request = urllib.request.Request(
        f"{REPORTING_URL}/reports/{day}",
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        result = json.load(response)

    logger.info(
        f"stored={result['stored']} emailed={result['emailed']} "
        f"summary_source={result['summary_source']}"
    )

    for warning in result["warnings"]:
        logger.warning(f"publish warning: {warning}")

    # The service degrades so a manual run still delivers the report one way or
    # the other. The scheduled run has to be stricter: the object is what this
    # DAG exists to produce, so a green task with nothing at the key would be a
    # lie. A failed email alone stays a warning.
    if not result["stored"]:
        raise RuntimeError(
            f"the report for {result['day']} was not stored at {result['key']}"
        )

    # The report is published either way, so this is not a lost run - but a
    # fallback narrative is a degraded one, and retrying is free: the key is
    # derived from the date, so a later attempt overwrites rather than
    # duplicates. This is what the retries below are actually for.
    if result["summary_source"] == FALLBACK_SUMMARY_SOURCE:
        raise RuntimeError(
            f"the report for {result['day']} was published with the fallback "
            f"narrative; the model did not answer"
        )

    logger.info(f"report for {result['day']} published to {result['key']}")

    return result["key"]


@dag(
    dag_id="daily_executive_report",
    schedule="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["module-5", "reporting", "langgraph"],
)
def daily_executive_report():
    """Build and publish the executive report for the run's logical date."""

    PythonOperator(
        task_id="build_report",
        python_callable=build_report,
        op_kwargs={"day": "{{ ds }}"},
    )


daily_executive_report()
