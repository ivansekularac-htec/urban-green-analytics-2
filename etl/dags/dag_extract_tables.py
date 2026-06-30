from datetime import timedelta

from airflow.sdk import dag, task
from extract.run_table import run_table
from extract.utils import get_tables_by_schedule
from pendulum import datetime

DAILY_SCHEDULE = "0 2 * * *"
HOURLY_SCHEDULE = "0 * * * *"


def create_extract_dag(
    dag_id: str,
    schedule: str,
    tags: list[str],
):
    @dag(
        dag_id=dag_id,
        schedule=schedule,
        start_date=datetime(2024, 1, 1, tz="UTC"),
        catchup=False,
        max_active_runs=1,
        tags=tags,
    )
    def extract_dag():
        """
        Extract incrementally updated PostgreSQL tables into MinIO.

        This DAG processes all tables configured for the given schedule.
        Each task performs an incremental extraction based on the configured
        cursor column, writes the data as Parquet, uploads it to MinIO, and
        advances the extraction cursor only after a successful upload.
        """

        tables = get_tables_by_schedule(schedule)

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

    return extract_dag()


app_extract_hourly = create_extract_dag(
    dag_id="app_extract_hourly",
    schedule=HOURLY_SCHEDULE,
    tags=["app", "extract", "hourly"],
)

app_extract_daily = create_extract_dag(
    dag_id="app_extract_daily",
    schedule=DAILY_SCHEDULE,
    tags=["app", "extract", "daily"],
)
