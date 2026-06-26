from datetime import datetime

from airflow.sdk import dag, task
from run_table import run_table
from utils import get_tables_by_schedule

HOURLY_SCHEDULE = "0 * * * *"


@dag(
    schedule="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["app", "extract", "hourly"],
)
def app_extract_hourly():
    """
    Extract incrementally updated hourly tables from PostgreSQL into MinIO.

    This DAG runs every hour and processes all tables configured with an
    hourly schedule. Each task performs an incremental extraction based on
    the configured cursor column, writes the data as Parquet, uploads it to
    the staging bucket in MinIO, and advances the extraction cursor only
    after a successful upload.
    """

    tables = get_tables_by_schedule(HOURLY_SCHEDULE)

    @task
    def run(table_config: dict):
        """
        Execute the extraction pipeline for a single table.

        Args:
            table_config: Configuration dictionary describing the source
                table, cursor column, partitioning strategy and schedule.
        """

        run_table(table_config)

    run.expand(table_config=tables)


app_extract_hourly()
