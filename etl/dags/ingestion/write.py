import os
from io import BytesIO

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

STAGING_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")
MINIO_CONN_ID = os.getenv("MINIO_CONN_ID", "urbangreen_minio")


def write_parquet(
    df: pd.DataFrame,
    table: str,
    object_key: str,
    partition_column: str | None = None,
) -> None:

    hook = S3Hook(aws_conn_id=MINIO_CONN_ID)

    if partition_column:
        for partition_value, group in df.groupby(partition_column):
            key = f"{table}/{partition_column}={partition_value}/{object_key}"

            upload_dataframe(hook, group, key)

    else:
        key = f"{table}/{object_key}"

        upload_dataframe(hook, df, key)


def upload_dataframe(
    hook: S3Hook,
    df: pd.DataFrame,
    object_key: str,
) -> None:

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
        replace=False,
    )
