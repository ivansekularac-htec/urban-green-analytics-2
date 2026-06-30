from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from extract_common.path_builder import (
    build_partitioned_object_key,
    build_table_object_key,
)
from extract_common.settings import MINIO_CONN_ID, MINIO_STAGING_BUCKET

logger = logging.getLogger(__name__)


def write_dataframe_to_minio(
    dataframe: pd.DataFrame,
    table: str,
    partition_column: str | None,
    partition_name: str | None,
    previous_cursor: dict[str, int],
    upper_cursor: dict[str, int],
) -> list[str]:
    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)
    object_keys: list[str] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        if partition_column is None:
            object_key = build_table_object_key(
                table=table,
                previous_cursor=previous_cursor,
                upper_cursor=upper_cursor,
            )
            local_path = temp_path / f"{table}.parquet"

            write_and_upload_parquet(
                dataframe=dataframe,
                local_path=local_path,
                object_key=object_key,
                s3=s3,
            )

            object_keys.append(object_key)
            return object_keys

        if partition_name is None:
            raise ValueError(
                "partition_name must be provided when partition_column is set."
            )

        partition_values = partition_values_from_epoch_seconds(
            dataframe[partition_column]
        )
        partitioned_dataframe = dataframe.assign(
            _extract_partition_value=partition_values
        )

        for partition_value, partition_df in partitioned_dataframe.groupby(
            "_extract_partition_value",
            dropna=False,
            sort=True,
        ):
            partition_value_as_text = str(partition_value)
            cleaned_partition_df = partition_df.drop(
                columns=["_extract_partition_value"]
            )

            object_key = build_partitioned_object_key(
                table=table,
                partition_name=partition_name,
                partition_value=partition_value_as_text,
                previous_cursor=previous_cursor,
                upper_cursor=upper_cursor,
            )

            local_path = (
                temp_path
                / f"{table}_{partition_name}_{partition_value_as_text}.parquet"
            )

            write_and_upload_parquet(
                dataframe=cleaned_partition_df,
                local_path=local_path,
                object_key=object_key,
                s3=s3,
            )

            object_keys.append(object_key)

    return object_keys


def write_and_upload_parquet(
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


def partition_values_from_epoch_seconds(series: pd.Series) -> pd.Series:
    # The project stores timestamps as BIGINT epoch seconds.
    return pd.to_datetime(series, unit="s", utc=True).dt.strftime("%Y-%m-%d")
