"""
parquet.py
Parquet serialization and MinIO upload utilities.

This module converts extracted DataFrames to Parquet, creates deterministic
object keys, applies optional date partitioning, and uploads the resulting
objects to the configured MinIO staging bucket.
"""

from __future__ import annotations

import logging
from io import BytesIO

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from postgres_extract.config import (
    POSTGRES_SCHEMA,
    STAGING_BUCKET,
)

logger = logging.getLogger(__name__)


def _build_partition_values(
    dataframe: pd.DataFrame,
    source_column: str,
    source_type: str,
) -> pd.Series:
    """
    Convert source partition values to UTC dates in YYYY-MM-DD format.
    """
    if source_column not in dataframe.columns:
        raise ValueError(
            f"Partition source column '{source_column}' "
            "does not exist in extracted dataframe."
        )

    if source_type == "epoch_seconds":
        timestamps = pd.to_datetime(
            dataframe[source_column],
            unit="s",
            utc=True,
            errors="coerce",
        )
    else:
        timestamps = pd.to_datetime(
            dataframe[source_column],
            utc=True,
            errors="coerce",
        )

    if timestamps.isna().any():
        invalid_count = int(timestamps.isna().sum())

        raise ValueError(
            f"Table contains {invalid_count} invalid values "
            f"in partition column '{source_column}'."
        )

    return timestamps.dt.strftime("%Y-%m-%d")


def _build_object_key(
    table_name: str,
    cursor_from: int,
    cursor_to: int,
    partition_column: str | None = None,
    partition_value: str | None = None,
    part_number: int | None = None,
) -> str:
    """
    Build a deterministic MinIO object key for one Parquet file.
    """
    base_key = (
        f"extract/{POSTGRES_SCHEMA}/{table_name}/"
        f"updated_at_from={cursor_from}/"
        f"updated_at_to={cursor_to}"
    )

    if part_number is None:
        file_name = f"{table_name}_{cursor_from}_{cursor_to}.parquet"
    else:
        file_name = f"part-{part_number:05d}.parquet"

    if partition_column and partition_value:
        return f"{base_key}/{partition_column}={partition_value}/{file_name}"

    return f"{base_key}/{file_name}"


def _upload_dataframe_as_parquet(
    s3_hook: S3Hook,
    table_name: str,
    dataframe: pd.DataFrame,
    cursor_from: int,
    cursor_to: int,
    partition_column: str | None = None,
    partition_value: str | None = None,
    part_number: int | None = None,
) -> str:
    """
    Serialize one DataFrame to Parquet and upload it to MinIO.
    """
    object_key = _build_object_key(
        table_name=table_name,
        cursor_from=cursor_from,
        cursor_to=cursor_to,
        partition_column=partition_column,
        partition_value=partition_value,
        part_number=part_number,
    )

    buffer = BytesIO()

    dataframe.to_parquet(
        buffer,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    buffer.seek(0)

    s3_hook.load_bytes(
        bytes_data=buffer.getvalue(),
        key=object_key,
        bucket_name=STAGING_BUCKET,
        replace=True,
    )

    logger.debug(
        "Uploaded Parquet object: bucket=%s key=%s rows=%s",
        STAGING_BUCKET,
        object_key,
        len(dataframe),
    )

    return object_key


def write_dataframe_to_minio(
    s3_hook: S3Hook,
    table_name: str,
    dataframe: pd.DataFrame,
    cursor_from: int,
    cursor_to: int,
    partition_config: dict[str, str] | None,
    part_number: int | None = None,
) -> int:
    """
    Write a DataFrame to MinIO, optionally split by a date partition.
    """
    if partition_config is None:
        _upload_dataframe_as_parquet(
            s3_hook=s3_hook,
            table_name=table_name,
            dataframe=dataframe,
            cursor_from=cursor_from,
            cursor_to=cursor_to,
            part_number=part_number,
        )

        return 1

    source_column = partition_config["source_column"]
    output_name = partition_config["output_name"]
    source_type = partition_config["source_type"]

    partition_values = _build_partition_values(
        dataframe=dataframe,
        source_column=source_column,
        source_type=source_type,
    )

    uploaded_objects = 0

    for partition_value in sorted(partition_values.unique()):
        partition_dataframe = dataframe.loc[partition_values == partition_value].copy()

        _upload_dataframe_as_parquet(
            s3_hook=s3_hook,
            table_name=table_name,
            dataframe=partition_dataframe,
            cursor_from=cursor_from,
            cursor_to=cursor_to,
            partition_column=output_name,
            partition_value=partition_value,
            part_number=part_number,
        )

        uploaded_objects += 1

    return uploaded_objects
