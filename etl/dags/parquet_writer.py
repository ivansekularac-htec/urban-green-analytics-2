import io
import logging
from typing import Any, Iterable, List, Optional, Tuple

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from config import BUCKET_NAME, MINIO_CONN_ID

logger = logging.getLogger(__name__)


def build_sorted_df(
    rows: List[tuple],
    columns: List[str],
    cursor_column: str,
    id_column: str,
) -> pd.DataFrame:
    """Create and sort DataFrame by cursor and id."""
    if cursor_column not in columns:
        raise KeyError(f"Cursor column '{cursor_column}' not found")

    df = pd.DataFrame(rows, columns=columns)
    return df.sort_values([cursor_column, id_column])


def extract_cursor_bounds(
    df: pd.DataFrame,
    cursor_column: str,
    id_column: str,
) -> Tuple[Tuple[Any, Any], Tuple[Any, Any]]:
    """Extract first and last cursor boundaries from sorted DataFrame."""
    first = df.iloc[0]
    last = df.iloc[-1]

    cursor_from = (first[cursor_column], first[id_column])
    cursor_to = (last[cursor_column], last[id_column])

    return cursor_from, cursor_to


def update_max_cursor(
    current_max: Tuple[Any, Any],
    new_cursor_to: Tuple[Any, Any],
) -> Tuple[Any, Any]:
    """Keep highest cursor based on tuple comparison."""
    if current_max == (None, None):
        return new_cursor_to
    return max(current_max, new_cursor_to)


def add_partition_column(
    df: pd.DataFrame,
    partition_column: Optional[str],
):
    """
    Add partition column and return grouped dataframe.
    If no partition column is provided, returns single group.
    """
    if partition_column and partition_column in df.columns:
        df = df.copy()
        df["_partition_day"] = pd.to_datetime(
            df[partition_column],
            unit="s",
            utc=True,
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        return df.groupby("_partition_day", sort=True)

    return [(None, df)]


def build_object_key(
    table_name: str,
    cursor_from: Tuple[Any, Any],
    cursor_to: Tuple[Any, Any],
    batch_index: int,
    partition_value: Optional[str] = None,
) -> str:
    """Generate S3 object key for parquet file."""
    filename = f"{table_name}_{cursor_from}_{cursor_to}_{batch_index}.parquet"

    if partition_value is None:
        return f"app/{table_name}/{filename}"

    return f"app/{table_name}/harvest_date={partition_value}/{filename}"


def upload_parquet(
    s3: S3Hook,
    buffer: io.BytesIO,
    bucket: str,
    key: str,
):
    """Upload parquet buffer to S3."""
    s3.load_file_obj(
        file_obj=buffer,
        key=key,
        bucket_name=bucket,
        replace=True,
    )


def write_batches(
    table_name: str,
    batch_iter: Iterable[Tuple[List[tuple], List[str]]],
    partition_column: Optional[str],
    cursor_column: str = "updated_at",
    id_column: str = "id",
):
    """
    Stream batches from Postgres extractor and upload Parquet files to MinIO via S3Hook.

    Each batch is written as a separate Parquet object in the staging bucket.
    When partitioning is enabled, rows are grouped by partition value and each
    group is uploaded as its own object.

    Returns:
        max_cursor (int), written rows: highest cursor value processed
    """

    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)
    bucket = BUCKET_NAME

    max_cursor = (None, None)
    batch_index = 0
    rows_written = 0

    for rows, columns in batch_iter:
        if not rows:
            continue

        df = build_sorted_df(rows, columns, cursor_column, id_column)

        cursor_from, cursor_to = extract_cursor_bounds(df, cursor_column, id_column)
        max_cursor = update_max_cursor(max_cursor, cursor_to)

        grouped = add_partition_column(df, partition_column)

        for partition_value, group in grouped:
            rows_written += len(group)

            buffer = io.BytesIO()
            group.to_parquet(
                buffer,
                engine="pyarrow",
                compression="snappy",
                index=False,
            )
            buffer.seek(0)

            object_key = build_object_key(
                table_name,
                cursor_from,
                cursor_to,
                batch_index,
                partition_value,
            )

            logger.info(
                "Writing %s rows for table '%s' to '%s'",
                len(group),
                table_name,
                object_key,
            )

            upload_parquet(s3, buffer, bucket, object_key)

            batch_index += 1

    return max_cursor, rows_written
