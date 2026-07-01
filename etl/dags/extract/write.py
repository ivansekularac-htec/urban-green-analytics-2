import io
import logging
from collections.abc import Iterable
from typing import Any
from uuid import uuid4

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from extract.utils import BUCKET_NAME, MINIO_CONN_ID, raw

logger = logging.getLogger(__name__)


def _update_max_cursor(
    current_max: Any,
    new_cursor_to: Any,
) -> Any:
    """Keep highest cursor based on tuple comparison."""
    return max(current_max, new_cursor_to)


def _build_object_key(
    table_name: str,
    batch_index: int,
    partition_value: str | None = None,
) -> str:
    """Generate S3 object key for parquet file."""
    base = raw("postgres", table_name)
    filename = f"{uuid4().hex}.parquet"

    if partition_value is None:
        return f"{base}/{filename}"

    return f"{base}/date={partition_value}/{filename}"


def _upload_parquet(
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
    batch_iter: Iterable[tuple[list[tuple], list[str]]],
    partition_column: str | None,
    cursor_column: str = "updated_at",
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

    max_cursor: Any = 0
    rows_written = 0

    for rows, columns in batch_iter:
        if not rows:
            continue

        batch_index = 0

        df = pd.DataFrame(rows, columns=columns)

        cursor_to = df[cursor_column].max()

        max_cursor = _update_max_cursor(max_cursor, cursor_to)

        if partition_column:
            ts = pd.to_datetime(
                df[partition_column],
                unit="s",
                utc=True,
                errors="coerce",
            )

            df["_partition"] = ts.dt.strftime("%Y-%m-%d")
            df["_partition"] = df["_partition"].fillna("unknown")

            groups = df.groupby("_partition", sort=True, dropna=False)
        else:
            df["_partition"] = None
            groups = [(None, df)]

        for partition_value, group in groups:
            clean_df = group.drop(columns=["_partition"])

            buffer = io.BytesIO()
            clean_df.to_parquet(
                buffer,
                engine="pyarrow",
                compression="snappy",
                index=False,
            )
            buffer.seek(0)

            object_key = _build_object_key(
                table_name,
                batch_index,
                partition_value,
            )

            logger.info(
                f"Writing {len(clean_df)} rows for table {table_name} to {object_key}"
            )

            _upload_parquet(s3, buffer, bucket, object_key)

            rows_written += len(clean_df)
            batch_index += 1

    return (
        str(max_cursor),
        rows_written,
    )
