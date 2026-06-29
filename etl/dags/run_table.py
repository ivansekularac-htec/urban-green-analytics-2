import logging

from airflow.exceptions import AirflowSkipException
from cursor import get_cursor, update_cursor
from extractor import extract_table
from parquet_writer import write_batches

logger = logging.getLogger(__name__)


def run_table(table_config: dict) -> None:
    """
    Execute the incremental extraction pipeline for a single table.

    The pipeline performs the following steps:

    1. Read the last successfully processed cursor from Airflow Variables.
    2. Extract rows whose cursor value is greater than the stored cursor.
    3. Write extracted rows as Parquet files and upload them to MinIO.
    4. Advance the cursor only after all writes complete successfully.

    If no new rows are found, the task is marked as skipped instead of
    succeeding with no output.

    Args:
        table_config:
            Configuration dictionary describing the source table, including
            its name, cursor column and optional partition column.

    Raises:
        AirflowSkipException:
            If no rows have changed since the previous successful extraction.
    """

    table_name = table_config["name"]
    cursor_column = table_config["cursor_column"]
    partition_column = table_config["partition_column"]

    cursor = get_cursor(table_name)

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
        raise AirflowSkipException(f"No new rows found for table '{table_name}'.")

    update_cursor(table_name, max_cursor)
