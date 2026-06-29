from datetime import timedelta

from airflow.sdk import dag, task
from pendulum import datetime
from run_table import run_table
from utils import get_tables_by_schedule

DAILY_SCHEDULE = "0 2 * * *"


@dag(
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["app", "extract", "daily"],
)
def app_extract_daily():
    """
    Extract incrementally updated daily tables from PostgreSQL into MinIO.

    This DAG runs once per day and processes all tables configured with a
    daily schedule. Each task performs an incremental extraction based on
    the configured cursor column, writes the data as Parquet, uploads it to
    the staging bucket in MinIO, and advances the extraction cursor only
    after a successful upload.
    """

    tables = get_tables_by_schedule(DAILY_SCHEDULE)

    @task(retries=2, retry_delay=timedelta(minutes=5))
    def extract(table_config: dict):
        """
        Execute the extraction pipeline for a single table.

        Args:
            table_config: Configuration dictionary describing the source
                table, cursor column, partitioning strategy and schedule.
        """
        run_table(table_config)

    for table in tables:
        extract.override(task_id=f"extract_{table['name']}")(table)


app_extract_daily()
