"""Airflow DAG for the daily executive report.

The pipeline itself is the LangGraph graph in the reporting service, so it can
be run and tested without a scheduler. This DAG supplies the schedule and the
report date, and records the object key the run published.
"""

import json
import logging
import urllib.request
from datetime import timedelta

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import dag

logger = logging.getLogger(__name__)

REPORTING_URL = "http://urbangreen-reporting:8002"

# The first inference after a container start loads the model, which takes far
# longer than a warm run.
REQUEST_TIMEOUT_SECONDS = 600


def build_report(day: str) -> str:
    """Ask the reporting service for one day's report.

    Args:
        day: Report date as YYYY-MM-DD.

    Returns:
        The object key the report was published under, which Airflow stores as
        the task result.
    """

    request = urllib.request.Request(
        f"{REPORTING_URL}/reports/{day}",
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        result = json.load(response)

    logger.info("report for %s published to %s", result["day"], result["key"])
    logger.info("stored=%s emailed=%s", result["stored"], result["emailed"])

    for warning in result["warnings"]:
        logger.warning("publish warning: %s", warning)

    return result["key"]


@dag(
    dag_id="daily_executive_report",
    schedule="0 6 * * *",
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
