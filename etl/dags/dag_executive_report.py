"""Daily Airflow wrapper around the executive report pipeline."""

from datetime import timedelta

import pendulum
from airflow.sdk import dag, get_current_context, task


@dag(
    dag_id="executive_report",
    schedule="0 9 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="Europe/Belgrade"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(minutes=12),
    },
    tags=["module-5", "report", "ollama"],
)
def executive_report():
    @task(task_id="run_report")
    def run_report_task() -> dict:
        from reports.graph import run_report

        report_date = get_current_context()["ds"]
        result = run_report(report_date)
        print(f"published object_key={result['object_key']}")
        return {
            "report_date": report_date,
            "html": result["html"],
            "object_key": result["object_key"],
        }

    @task(task_id="send_email", execution_timeout=timedelta(minutes=2))
    def send_email_task(payload: dict) -> str:
        from reports.email import send_report_email

        send_report_email(payload["html"], payload["report_date"])
        return payload["object_key"]

    send_email_task(run_report_task())


executive_report()