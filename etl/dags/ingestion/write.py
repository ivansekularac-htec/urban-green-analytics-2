import os
from io import BytesIO

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

STAGING_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")
MINIO_CONN_ID = os.getenv("MINIO_CONN_ID", "urbangreen_minio")
OBJECT_PREFIX = "raw/postgres"


def write_parquet(
    df: pd.DataFrame,
    table: str,
    part: int,
    partition_column: str | None = None,
) -> None:
    """
    Writes a DataFrame chunk to MinIO (S3-compatible storage) as Parquet.

    This function is responsible for translating extracted relational data
    into a lake-friendly object layout.

    Responsibilities:
    - Convert DataFrame into Parquet format
    - Build deterministic object storage keys
    - Apply optional partitioning logic
    - Upload data to MinIO via S3Hook

    Partitioning behavior:
    - If `partition_column` is provided:
        * Data is grouped by that column
        * Each group is written as a separate Parquet object
        * Objects are stored under a partitioned directory structure

    - If `partition_column` is None:
        * Entire chunk is written as a single Parquet object

    Object key format:
        - Non-partitioned:
            {table}/{cursor_column}=start_end.parquet

        - Partitioned:
            {table}/{partition_column}=value/{cursor_column}=start_end.parquet

    Args:
        df (pd.DataFrame): Chunk of extracted data
        table (str): Source table name
        cursor_column (str): Column used for incremental tracking
        partition_column (str | None): Optional column used for partitioning output
    """

    hook = S3Hook(aws_conn_id=MINIO_CONN_ID)

    # ---------------------------------------------------------
    # Partitioned write (multiple files per chunk)
    # ---------------------------------------------------------
    if partition_column:
        df = df.copy()

        # Convert Unix timestamp → date partition
        df["partition_day"] = pd.to_datetime(
            df[partition_column], unit="s"
        ).dt.strftime("%Y-%m-%d")

        for partition_value, group in df.groupby("partition_day"):
            object_key = (
                f"{OBJECT_PREFIX}/"
                f"{table}/"
                f"{partition_column}={partition_value}/"
                f"part-{part:06d}.parquet"
            )

            upload_dataframe(hook, group, object_key)

    # ---------------------------------------------------------
    # Non-partitioned write (single file per chunk)
    # ---------------------------------------------------------
    else:
        object_key = f"{OBJECT_PREFIX}/{table}/part-{part:06d}.parquet"

        upload_dataframe(hook, df, object_key)


def upload_dataframe(
    hook: S3Hook,
    df: pd.DataFrame,
    object_key: str,
) -> None:
    """
    Converts a DataFrame into Parquet format and uploads it to MinIO.

    This function is intentionally minimal and stateless:
    it does not perform any business logic, partitioning,
    or naming decisions.

    Args:
        hook (S3Hook): Initialized Airflow S3/MinIO hook
        df (pd.DataFrame): Data to serialize
        object_key (str): Full destination path inside the bucket
    """

    buffer = BytesIO()

    df.to_parquet(
        buffer,
        engine="pyarrow",
        index=False,
    )

    buffer.seek(0)

    hook.load_bytes(
        bytes_data=buffer.getvalue(),
        key=object_key,
        bucket_name=STAGING_BUCKET,
        replace=True,
    )
