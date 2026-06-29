import io
import logging
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Sequence, Tuple

import pyarrow as pa
import pyarrow.parquet as pq
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from config import BUCKET_NAME, MINIO_CONN_ID

logger = logging.getLogger(__name__)


def _partition_rows(
    rows: Sequence[Tuple],
    columns: Sequence[str],
    partition_column: Optional[str],
) -> List[Tuple[Tuple, Optional[object]]]:
    if partition_column is None or partition_column not in columns:
        return [(tuple(rows), None)]

    partition_idx = columns.index(partition_column)
    partitioned_rows = {}

    for row in rows:
        value = row[partition_idx]

        if isinstance(value, datetime):
            partition_key = value.date()
        elif isinstance(value, (int, float)):
            partition_key = datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            ).date()
        else:
            partition_key = value

        partitioned_rows.setdefault(partition_key, []).append(row)

    return [
        (tuple(group), partition_key)
        for partition_key, group in partitioned_rows.items()
    ]


def _format_partition_value(partition_value: object) -> str:
    if isinstance(partition_value, datetime):
        return partition_value.strftime("%Y-%m-%d")

    if isinstance(partition_value, (int, float)):
        return datetime.fromtimestamp(partition_value, tz=timezone.utc).strftime(
            "%Y-%m-%d"
        )

    return str(partition_value)


def write_batches(
    table_name: str,
    batch_iter: Iterable[Tuple[List[tuple], List[str]]],
    partition_column: Optional[str],
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

    hook = S3Hook(aws_conn_id=MINIO_CONN_ID)

    bucket = BUCKET_NAME

    max_cursor = -1
    batch_index = 0
    rows_written = 0

    for rows, columns in batch_iter:
        if not rows:
            continue

        if cursor_column not in columns:
            raise KeyError(
                f"Cursor column '{cursor_column}' not found in table columns"
            )

        logger.info(
            "Processing batch for table '%s': %s rows with cursor column '%s'",
            table_name,
            len(rows),
            cursor_column,
        )

        cursor_idx = columns.index(cursor_column)
        cursor_from = rows[0][cursor_idx]
        cursor_to = rows[-1][cursor_idx]
        max_cursor = max(max_cursor, cursor_to)

        partitioned_groups = _partition_rows(rows, columns, partition_column)

        for group_rows, partition_value in partitioned_groups:
            rows_written += len(group_rows)

            table = pa.Table.from_arrays(list(zip(*group_rows)), names=columns)

            buffer = io.BytesIO()
            pq.write_table(table, buffer, compression="snappy")
            buffer.seek(0)

            if partition_column is None or partition_column not in columns:
                object_key = (
                    f"app/{table_name}/"
                    f"{table_name}_{cursor_from}_{cursor_to}_{batch_index}.parquet"
                )
            else:
                partition_date = _format_partition_value(partition_value)
                object_key = (
                    f"app/{table_name}/"
                    f"harvest_date={partition_date}/"
                    f"{table_name}_{cursor_from}_{cursor_to}_{batch_index}.parquet"
                )

            logger.info(
                "Writing %s rows for table '%s' to MinIO path '%s'",
                len(group_rows),
                table_name,
                object_key,
            )

            try:
                hook.load_file_obj(
                    file_obj=buffer,
                    key=object_key,
                    bucket_name=bucket,
                    replace=True,
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to upload parquet object '{object_key}' for table '{table_name}': {exc}"
                ) from exc

            batch_index += 1

    return max_cursor, rows_written
