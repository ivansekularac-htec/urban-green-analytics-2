"""Daily DAG that runs the executive report pipeline (T5.3.2).

The DAG only schedules and observes the pipeline; the work lives in the `report`
package beside it. It derives the report date from the run's logical date, so a
backfill or a manual run for any day reports that day, and it reaches ClickHouse,
Ollama, MinIO and Mailpit over the compose network - ClickHouse and MinIO from
the seeded connections, Ollama and the mail sink from `OLLAMA_*` / `SMTP_*` env.

Retries cover a cold model load. They are only useful if a failure surfaces, so
the task fails on a fallback summary rather than publishing a degraded report and
going green: a green run therefore means the model wrote the prose, and the retry
has something to fire on when it did not.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.exceptions import AirflowException
from airflow.sdk import dag, get_current_context, task

_DAGS_DIR = str(Path(__file__).resolve().parent)
if _DAGS_DIR not in sys.path:
    sys.path.insert(0, _DAGS_DIR)

logger = logging.getLogger(__name__)


@dag(
    dag_id="daily_executive_report",
    schedule="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["module-5", "reporting", "langgraph", "llm"],
)
def daily_executive_report():
    """Build and publish the executive report for the run's date."""

    @task(task_id="build_report")
    def build_report() -> str:
        # Imported here rather than at module load so DAG parsing stays light and
        # does not pull in langgraph on every scheduler scan.
        from report.deps import from_airflow
        from report.graph import run_report
        from report.nodes.summarize import SOURCE_FALLBACK

        report_date = get_current_context()["ds"]

        result = run_report(from_airflow(), report_date)
        object_key = result.get("object_key")

        logger.info(
            f"report for {report_date}: key={object_key} "
            f"summary={result.get('summary_source')} email_sent={result.get('email_sent')}"
        )

        if result.get("summary_source") == SOURCE_FALLBACK:
            # The object exists, but the model did not write it. Fail so the
            # retry can try a warm model; a green run means real prose.
            raise AirflowException(
                f"summary fell back to fixed text for {report_date}; failing so the retry can fire"
            )

        return object_key

    build_report()


daily_executive_report()
