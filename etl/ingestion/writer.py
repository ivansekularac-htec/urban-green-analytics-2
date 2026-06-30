"""
Writer layer for ingestion pipeline.

Responsible for:
- Converting extracted DataFrames into Parquet
- Handling optional partitioning
- Uploading Parquet bytes to object storage (MinIO/S3)
"""

from io import BytesIO

import pandas as pd

from ingestion.object_keys import build_object_key
from ingestion.storage import upload_parquet


def write_dataframe(df, config, start_cursor, end_cursor):
    """
    Writes a single extraction batch to MinIO.

    Supports:
        - Non-partitioned tables → one Parquet object
        - Partitioned tables → one Parquet object per partition

    Each object key encodes the composite cursor range
    (updated_at + id) represented by this batch, making
    uploads deterministic and idempotent.

    Args:
        df (pd.DataFrame):
            Batch returned from Postgres.

        config (dict):
            Table ingestion configuration.

        start_cursor (dict):
            Composite cursor for the first row in the batch.

        end_cursor (dict):
            Composite cursor for the last row in the batch.
    """

    table = config["table"]
    bucket = config["bucket"]
    partition_column = config.get("partition_column")

    # ---------------------------------------------------------
    # NON-PARTITIONED TABLES
    # ---------------------------------------------------------
    if not partition_column:
        buffer = BytesIO()

        df.to_parquet(
            buffer,
            index=False,
        )

        object_key = build_object_key(
            table=table,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
        )

        upload_parquet(
            parquet_bytes=buffer.getvalue(),
            bucket=bucket,
            object_key=object_key,
        )

        return

    # ---------------------------------------------------------
    # PARTITIONED TABLES
    # ---------------------------------------------------------

    partitioned_df = df.copy()

    # Convert epoch timestamp into YYYY-MM-DD partition
    partitioned_df["_partition_date"] = pd.to_datetime(
        partitioned_df[partition_column],
        unit="s",
        utc=True,
    ).dt.strftime("%Y-%m-%d")

    # Write one object per partition
    for partition_date, partition_df in partitioned_df.groupby("_partition_date"):
        partition_df = partition_df.drop(columns="_partition_date")

        buffer = BytesIO()

        partition_df.to_parquet(
            buffer,
            index=False,
        )

        object_key = build_object_key(
            table=table,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
            partition_column=partition_column,
            partition_value=partition_date,
        )

        print(f"[{table}] Uploading partition {partition_date}")

        upload_parquet(
            parquet_bytes=buffer.getvalue(),
            bucket=bucket,
            object_key=object_key,
        )

        print(f"[{table}] Uploaded partition {partition_date}")
