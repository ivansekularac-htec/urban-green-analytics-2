"""Daily Airflow DAG for the UrbanGreen executive report."""

import logging
from datetime import timedelta

import pendulum
from airflow.sdk import dag, get_current_context, task

from reports.pipeline import run_report

logger = logging.getLogger(__name__)


@dag(
    dag_id="daily_executive_report",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=3),
    },
    tags=["module-5", "reporting", "langgraph"],
)
def daily_executive_report():
    """Generate the report for the calendar day represented by the run."""

    @task(
        task_id="build_and_publish_report",
        execution_timeout=timedelta(minutes=10),
    )
    def build_and_publish_report() -> str:
        """Invoke the graph and return its deterministic MinIO object key."""

        context = get_current_context()
        # For a scheduled run, Airflow's logical date is the start of the
        # completed data interval. It is therefore already the report date;
        # subtracting another day would make every scheduled report stale.
        report_date = context["logical_date"].date()
        logger.info("Starting scheduled executive report for %s", report_date)

        result = run_report(report_date)
        object_key = result["object_key"]
        object_uri = f"s3://{result['published_bucket']}/{object_key}"

        logger.info("Executive report is available at %s", object_uri)
        return object_key

    build_and_publish_report()


daily_executive_report_dag = daily_executive_report()
