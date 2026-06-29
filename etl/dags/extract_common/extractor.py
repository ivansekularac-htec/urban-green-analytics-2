from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.providers.postgres.hooks.postgres import PostgresHook

from extract_common.cursor import cursor_variable_key, get_cursor, set_cursor
from extract_common.minio_writer import write_dataframe_to_minio
from extract_common.postgres_reader import (
    assert_table_shape,
    get_run_cutoff,
    get_upper_cursor,
    read_changed_rows_in_chunks,
)
from extract_common.settings import POSTGRES_CONN_ID
from extract_common.validation import normalize_config, validate_config

logger = logging.getLogger(__name__)


def extract_table_to_minio(table_config: dict[str, Any]) -> dict[str, Any]:
    """Extract changed rows from one app table and land them as Parquet in MinIO."""
    config = normalize_config(table_config)
    validate_config(config)

    table_name = config["name"]
    schema = config["schema"]
    cursor_column = config["cursor_column"]
    primary_key = config["primary_key"]
    partition_column = config.get("partition_column")
    partition_name = config.get("partition_name") or partition_column

    cursor_key = cursor_variable_key(schema=schema, table=table_name)
    previous_cursor = get_cursor(cursor_key)

    postgres = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    assert_table_shape(
        postgres=postgres,
        schema=schema,
        table=table_name,
        primary_key=primary_key,
        cursor_column=cursor_column,
        partition_column=partition_column,
    )

    run_cutoff = get_run_cutoff(postgres)

    upper_cursor = get_upper_cursor(
        postgres=postgres,
        schema=schema,
        table=table_name,
        cursor_column=cursor_column,
        primary_key=primary_key,
        previous_cursor=previous_cursor,
        run_cutoff=run_cutoff,
    )

    if upper_cursor is None:
        message = (
            f"No changed rows for {schema}.{table_name} after cursor {previous_cursor} "
            f"with run_cutoff={run_cutoff}. Marking task as skipped."
        )
        logger.info(message)
        raise AirflowSkipException(message)

    object_keys: list[str] = []
    total_rows = 0
    chunk_count = 0
    chunk_previous_cursor = previous_cursor

    for dataframe_chunk in read_changed_rows_in_chunks(
        postgres=postgres,
        schema=schema,
        table=table_name,
        cursor_column=cursor_column,
        primary_key=primary_key,
        previous_cursor=previous_cursor,
        upper_cursor=upper_cursor,
    ):
        if dataframe_chunk.empty:
            continue

        chunk_count += 1
        total_rows += len(dataframe_chunk)

        chunk_upper_cursor = build_chunk_upper_cursor(
            dataframe=dataframe_chunk,
            cursor_column=cursor_column,
            primary_key=primary_key,
        )

        chunk_object_keys = write_dataframe_to_minio(
            dataframe=dataframe_chunk,
            table=table_name,
            partition_column=partition_column,
            partition_name=partition_name,
            previous_cursor=chunk_previous_cursor,
            upper_cursor=chunk_upper_cursor,
        )

        object_keys.extend(chunk_object_keys)

        # Move the in-memory chunk cursor only after this chunk is uploaded successfully.
        # The Airflow cursor variable is still updated only after all chunks succeed.
        chunk_previous_cursor = chunk_upper_cursor

    if total_rows == 0:
        message = (
            f"Upper cursor {upper_cursor} existed for {schema}.{table_name}, "
            "but no rows were read. Marking task as skipped."
        )
        logger.info(message)
        raise AirflowSkipException(message)

    # Critical ordering: advance the cursor only after every Parquet upload succeeds.
    set_cursor(cursor_key, upper_cursor)

    result = {
        "table": f"{schema}.{table_name}",
        "rows": total_rows,
        "chunks": chunk_count,
        "previous_cursor": previous_cursor,
        "new_cursor": upper_cursor,
        "object_keys": object_keys,
    }

    logger.info("Extract completed: %s", json.dumps(result, sort_keys=True))
    return result


def build_chunk_upper_cursor(
    dataframe: pd.DataFrame,
    cursor_column: str,
    primary_key: str,
) -> dict[str, int]:
    """Build the upper cursor for one already ordered DataFrame chunk."""
    last_row = dataframe.iloc[-1]

    return {
        "updated_at": int(last_row[cursor_column]),
        "id": int(last_row[primary_key]),
    }
