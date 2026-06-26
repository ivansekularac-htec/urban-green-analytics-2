import io
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from config import BUCKET_NAME, MINIO_CONN_ID


def write_batches(
    table_name: str,
    batch_iter,
    partition_column: str,
):
    """
    Stream batches from Postgres extractor and upload Parquet files to MinIO via S3Hook.

    Each batch is written as a separate Parquet object in the staging bucket.

    Returns:
        max_cursor (int): highest updated_at value processed
    """

    hook = S3Hook(aws_conn_id=MINIO_CONN_ID)

    bucket = BUCKET_NAME

    max_cursor = -1
    batch_index = 0

    rows_written = 0

    for rows, columns in batch_iter:
        if not rows:
            continue

        rows_written += len(rows)

        # Convert to Arrow table
        table = pa.Table.from_arrays(list(zip(*rows)), names=columns)

        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)

        updated_idx = columns.index("updated_at")

        cursor_from = rows[0][updated_idx]
        cursor_to = rows[-1][updated_idx]

        max_cursor = max(max_cursor, cursor_to)

        if partition_column is None:
            object_key = (
                f"app/{table_name}/"
                f"{table_name}_{cursor_from}_{cursor_to}_{batch_index}.parquet"
            )
        else:
            partition_idx = columns.index(partition_column)
            partition_timestamp = rows[0][partition_idx]

            partition_date = datetime.fromtimestamp(
                partition_timestamp,
                tz=timezone.utc,
            ).strftime("%Y-%m-%d")

            object_key = (
                f"app/{table_name}/"
                f"created_at={partition_date}/"
                f"{table_name}_{cursor_from}_{cursor_to}_{batch_index}.parquet"
            )

        # Upload to MinIO
        hook.load_file_obj(
            file_obj=buffer,
            key=object_key,
            bucket_name=bucket,
            replace=True,
        )

        batch_index += 1

    return max_cursor, rows_written
