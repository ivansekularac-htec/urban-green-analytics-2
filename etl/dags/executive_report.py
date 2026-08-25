"""Daily Airflow DAG for the UrbanGreen executive report."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import dag, get_current_context, task

_DAGS_DIR = str(Path(__file__).resolve().parent)

if _DAGS_DIR not in sys.path:
    sys.path.insert(0, _DAGS_DIR)

from report.pipeline import run_report


@dag(
    dag_id="executive_report",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=1)},
    tags=[
        "module-5",
        "reporting",
        "langgraph",
        "ollama",
    ],
)
def executive_report():
    """Generate and publish the daily executive report."""

    @task(task_id="generate_report")
    def generate_report():
        context = get_current_context()

        report_date = context["data_interval_start"].date().isoformat()

        return run_report(report_date)

    generate_report()


executive_report()
