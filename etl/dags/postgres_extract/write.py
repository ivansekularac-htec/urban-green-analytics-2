from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

MINIO_CONN_ID = "urbangreen_minio"
MINIO_BUCKET = "staging"
BASE_PREFIX = "app/raw/postgres"


def _write_parquet_to_minio(df: pd.DataFrame, key: str) -> None:
    hook = S3Hook(aws_conn_id=MINIO_CONN_ID)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / Path(key).name
        df.to_parquet(path, engine="pyarrow", index=False)
        hook.load_file(
            filename=str(path),
            key=key,
            bucket_name=MINIO_BUCKET,
            replace=True,
        )


def _build_object_key(
    table_name: str,
    cursor_from: int | None,
    cursor_to: int,
    partition_column: str | None = None,
    partition_value: str | None = None,
    part_number: int | None = None,
) -> str:
    cursor_from_value = 0 if cursor_from is None else cursor_from
    base_key = (
        f"{BASE_PREFIX}/{table_name}/"
        f"updated_at_from={cursor_from_value}/"
        f"updated_at_to={cursor_to}"
    )

    if part_number is None:
        file_name = f"{table_name}_{cursor_from_value}_{cursor_to}.parquet"
    else:
        file_name = f"part-{part_number:05d}.parquet"

    if partition_column and partition_value:
        return f"{base_key}/{partition_column}={partition_value}/{file_name}"

    return f"{base_key}/{file_name}"


def write_table(
    table: str,
    columns: list[str],
    rows: list[tuple],
    cursor_from: int | None,
    cursor_to: int,
    partition_by: str | None = None,
    partition_label: str | None = None,
) -> list[str]:
    df = pd.DataFrame(rows, columns=columns)
    file_keys: list[str] = []

    if table == "harvests" and partition_by == "created_at" and partition_label:
        df[partition_label] = pd.to_datetime(
            df[partition_by],
            unit="s",
            utc=True,
        ).dt.date.astype(str)

        for part_number, (partition_value, group) in enumerate(
            df.groupby(partition_label), start=1
        ):
            key = _build_object_key(
                table_name=table,
                cursor_from=cursor_from,
                cursor_to=cursor_to,
                partition_column=partition_label,
                partition_value=partition_value,
                part_number=part_number,
            )
            _write_parquet_to_minio(group.drop(columns=[partition_label]), key)
            file_keys.append(key)
    else:
        key = _build_object_key(
            table_name=table,
            cursor_from=cursor_from,
            cursor_to=cursor_to,
        )
        _write_parquet_to_minio(df, key)
        file_keys.append(key)

    return file_keys
