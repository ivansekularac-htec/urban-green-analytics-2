from datetime import timedelta

from airflow.exceptions import AirflowSkipException
from airflow.sdk import dag, task
from extract.cursor import get_cursor, update_cursor
from extract.extract import extract_table
from extract.utils import get_tables_by_cadence
from extract.write import write_batches
from pendulum import datetime

CADENCE_CRON = {
    "daily": "0 2 * * *",
    "hourly": "0 * * * *",
}


def create_extract_dag(
    dag_id: str,
    cadence: str,
    tags: list[str],
):
    @dag(
        dag_id=dag_id,
        schedule=CADENCE_CRON[cadence],
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

        tables = get_tables_by_cadence(cadence)

        @task(retries=2, retry_delay=timedelta(minutes=5))
        def extract(table_config: dict):
            """
            Execute the incremental extraction pipeline for a single table.

            The task performs the following steps:

            1. Read the last successfully processed cursor.
            2. Extract rows newer than the stored cursor.
            3. Write the extracted rows as Parquet files to MinIO.
            4. Update the cursor only after all files are written successfully.

            If no new rows are found, the task is marked as skipped.

            Args:
                table_config:
                    Configuration dictionary describing the source table,
                    including its name, cursor column and optional partition
                    column.

            Raises:
                AirflowSkipException:
                    If no new rows have been extracted.
            """
            table_name = table_config["name"]
            cursor_column = table_config["cursor_column"]
            partition_column = table_config["partition_column"]

            cursor = get_cursor(table_config)

            batch_iter = extract_table(
                table_name=table_name,
                cursor=cursor,
                cursor_column=cursor_column,
            )

            max_cursor, rows_written = write_batches(
                table_name=table_name,
                batch_iter=batch_iter,
                partition_column=partition_column,
                cursor_column=cursor_column,
            )

            if rows_written == 0:
                raise AirflowSkipException(
                    f"No new rows found for table '{table_name}'."
                )

            update_cursor(table_config, max_cursor)

        for table in tables:
            extract.override(task_id=f"extract_{table['name']}")(table)

    return extract_dag()


app_extract_hourly = create_extract_dag(
    dag_id="app_extract_hourly",
    cadence="hourly",
    tags=["app", "extract", "hourly"],
)

app_extract_daily = create_extract_dag(
    dag_id="app_extract_daily",
    cadence="daily",
    tags=["app", "extract", "daily"],
)
