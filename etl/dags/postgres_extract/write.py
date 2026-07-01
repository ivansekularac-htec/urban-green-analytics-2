from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

logger = logging.getLogger(__name__)

MINIO_CONN_ID = os.getenv("MINIO_CONN_ID", "urbangreen_minio")
MINIO_STAGING_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")
MINIO_STAGING_PREFIX = os.getenv("MINIO_STAGING_PREFIX", "app/raw/postgres").strip("/")


def write_dataframe_to_minio(
    dataframe: pd.DataFrame,
    table: str,
    partition_column: str | None,
    partition_name: str | None,
    previous_cursor: str,
    upper_cursor: str,
    part_number: int,
) -> list[str]:
    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)
    object_keys: list[str] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        if partition_column is None:
            object_key = table_object_key(
                table=table,
                previous_cursor=previous_cursor,
                upper_cursor=upper_cursor,
                part_number=part_number,
            )
            local_path = temp_path / f"{table}.parquet"

            upload_parquet(dataframe, local_path, object_key, s3)
            object_keys.append(object_key)

            return object_keys

        partition_name = partition_name or partition_column

        partition_values = pd.to_datetime(
            dataframe[partition_column],
            unit="s",
            utc=True,
        ).dt.strftime("%Y-%m-%d")

        partitioned_dataframe = dataframe.assign(_partition_value=partition_values)

        for partition_value, partition_df in partitioned_dataframe.groupby(
            "_partition_value",
            sort=True,
            dropna=False,
        ):
            clean_dataframe = partition_df.drop(columns=["_partition_value"])

            object_key = partitioned_object_key(
                table=table,
                partition_name=partition_name,
                partition_value=str(partition_value),
                previous_cursor=previous_cursor,
                upper_cursor=upper_cursor,
                part_number=part_number,
            )

            local_path = temp_path / f"{table}_{partition_value}.parquet"

            upload_parquet(clean_dataframe, local_path, object_key, s3)
            object_keys.append(object_key)

    return object_keys


def upload_parquet(
    dataframe: pd.DataFrame,
    local_path: Path,
    object_key: str,
    s3: S3Hook,
) -> None:
    dataframe.to_parquet(local_path, engine="pyarrow", index=False)

    s3.load_file(
        filename=str(local_path),
        key=object_key,
        bucket_name=MINIO_STAGING_BUCKET,
        replace=True,
    )

    logger.info(
        f"Uploaded {len(dataframe)} rows to s3://{MINIO_STAGING_BUCKET}/{object_key}"
    )


def table_object_key(
    table: str,
    previous_cursor: str,
    upper_cursor: str,
    part_number: int,
) -> str:
    return (
        f"{MINIO_STAGING_PREFIX}/{table}/"
        f"{range_path(previous_cursor, upper_cursor)}/"
        f"part={part_number:06d}.parquet"
    )


def partitioned_object_key(
    table: str,
    partition_name: str,
    partition_value: str,
    previous_cursor: str,
    upper_cursor: str,
    part_number: int,
) -> str:
    return (
        f"{MINIO_STAGING_PREFIX}/{table}/"
        f"{partition_name}={partition_value}/"
        f"{range_path(previous_cursor, upper_cursor)}/"
        f"part={part_number:06d}.parquet"
    )


def range_path(
    previous_cursor: str,
    upper_cursor: str,
) -> str:
    return f"from_updated_at={previous_cursor}/to_updated_at={upper_cursor}"
