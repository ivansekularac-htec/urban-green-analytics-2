"""Daily Airflow DAG for the UrbanGreen executive report."""

import logging
from datetime import timedelta

import pendulum
from airflow.sdk import dag, get_current_context, task

from reports.pipeline import run_report

logger = logging.getLogger(__name__)


@dag(
    dag_id="executive_report",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 8, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    tags=["urbangreen", "reporting"],
)
def executive_report():
    """Generate and publish the daily executive report."""

    @task(retries=2, retry_delay=timedelta(minutes=2))
    def generate_report() -> str:
        """Run the report pipeline for the previous day."""

        context = get_current_context()
        report_date = (context["logical_date"].date() - timedelta(days=1)).isoformat()

        logger.info(f"Running executive report for {report_date}")

        result = run_report(report_date)
        object_key = result["object_key"]
        object_uri = f"s3://{result['published_bucket']}/{object_key}"

        logger.info(f"Published executive report: {object_uri}")
        return object_key

    generate_report()


executive_report()
