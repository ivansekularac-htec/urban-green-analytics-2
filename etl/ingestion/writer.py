"""
Writer layer for ingestion pipeline.

Responsible for:
- Converting extracted DataFrames into Parquet files
- Handling optional partitioning logic
- Uploading files to object storage (MinIO/S3)
"""

import os

import pandas as pd

from ingestion.object_keys import build_object_key
from ingestion.storage import upload_parquet

# -------------------------------------------------
# ENV CONFIG (fallback if config does not provide it)
# -------------------------------------------------
DEFAULT_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")


def write_dataframe(df, config, cursor_start, cursor_end):
    """
    Writes extracted DataFrame to MinIO as Parquet files.

    Supports:
    - Non-partitioned tables → single file per batch
    - Partitioned tables → one file per partition value

    Args:
        df (pd.DataFrame): Extracted dataset
        config (dict): Table ingestion configuration
        cursor_start (int): Previous cursor value
        cursor_end (int): New cursor value
    """

    table = config["table"]

    # Use env fallback if bucket not explicitly set in config
    bucket = config.get("bucket", DEFAULT_BUCKET)

    partition_column = config.get("partition_column")

    # =====================================================
    # CASE 1: NON-PARTITIONED TABLES
    # =====================================================
    if not partition_column:
        parquet_path = f"/tmp/{table}_{cursor_end}.parquet"

        df.to_parquet(parquet_path, index=False)

        object_key = build_object_key(
            table=table,
            cursor_start=cursor_start,
            cursor_end=cursor_end,
        )

        upload_parquet(
            parquet_path=parquet_path,
            bucket=bucket,
            object_key=object_key,
        )

        return

    # =====================================================
    # CASE 2: PARTITIONED TABLES
    # =====================================================

    # Create safe copy so we don't mutate original DataFrame
    partitioned_df = df.copy()

    # Convert epoch → YYYY-MM-DD partition format
    partitioned_df["_partition_date"] = pd.to_datetime(
        partitioned_df[partition_column],
        unit="s",
        utc=True,
    ).dt.strftime("%Y-%m-%d")

    # Group by partition
    for partition_date, partition_df in partitioned_df.groupby("_partition_date"):
        # Clean helper column before writing
        partition_df = partition_df.drop(columns="_partition_date")

        parquet_path = (
            f"/tmp/{table}_{partition_date}_{cursor_start}_{cursor_end}.parquet"
        )

        partition_df.to_parquet(parquet_path, index=False)

        object_key = build_object_key(
            table=table,
            cursor_start=cursor_start,
            cursor_end=cursor_end,
            partition_column=partition_column,
            partition_value=partition_date,
        )

        print(f"[{table}] Uploading partition {partition_date}")

        upload_parquet(
            parquet_path=parquet_path,
            bucket=bucket,
            object_key=object_key,
        )

        print(f"[{table}] Uploaded partition {partition_date}")
