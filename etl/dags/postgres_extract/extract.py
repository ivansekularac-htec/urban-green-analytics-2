from __future__ import annotations

import json
import logging
import os
from typing import Any

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.providers.postgres.hooks.postgres import PostgresHook

from postgres_extract.cursor import cursor_key, get_cursor, set_cursor
from postgres_extract.write import write_dataframe_to_minio

logger = logging.getLogger(__name__)

POSTGRES_CONN_ID = os.getenv("POSTGRES_EXTRACT_CONN_ID", "urbangreen_db")
EXTRACT_CHUNK_SIZE = int(os.getenv("EXTRACT_CHUNK_SIZE", "100000"))


def extract_table(table_config: dict[str, Any]) -> dict[str, Any]:
    schema = table_config.get("schema", "app")
    table = table_config["name"]
    cursor_column = table_config.get("cursor_column", "updated_at")
    partition_column = table_config.get("partition_column")
    partition_name = table_config.get("partition_name") or partition_column

    cursor_variable = cursor_key(schema=schema, table=table)
    previous_cursor = get_cursor(cursor_variable)

    postgres = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    upper_cursor = get_upper_cursor(
        postgres=postgres,
        schema=schema,
        table=table,
        cursor_column=cursor_column,
        previous_cursor=previous_cursor,
    )

    if upper_cursor is None:
        message = (
            f"No changed rows for {schema}.{table} after cursor {previous_cursor}."
        )
        logger.info(message)
        raise AirflowSkipException(message)

    sql = f"""
        SELECT *
        FROM {schema}.{table}
        WHERE {cursor_column} > %(last_updated_at)s::BIGINT
          AND {cursor_column} <= %(upper_updated_at)s::BIGINT
    """

    params = {
        "last_updated_at": previous_cursor,
        "upper_updated_at": upper_cursor,
    }

    if partition_column is not None:
        result = extract_partitioned_table(
            postgres=postgres,
            sql=sql,
            params=params,
            schema=schema,
            table=table,
            cursor_column=cursor_column,
            partition_column=partition_column,
            partition_name=partition_name,
            previous_cursor=previous_cursor,
            upper_cursor=upper_cursor,
        )
    else:
        result = extract_non_partitioned_table(
            postgres=postgres,
            sql=sql,
            params=params,
            schema=schema,
            table=table,
            cursor_column=cursor_column,
            previous_cursor=previous_cursor,
            upper_cursor=upper_cursor,
        )

    set_cursor(cursor_variable, upper_cursor)

    logger.info(f"Extract completed: {json.dumps(result, sort_keys=True)}")

    return result


def extract_partitioned_table(
    postgres: PostgresHook,
    sql: str,
    params: dict[str, str],
    schema: str,
    table: str,
    cursor_column: str,
    partition_column: str,
    partition_name: str | None,
    previous_cursor: str,
    upper_cursor: str,
) -> dict[str, Any]:
    connection = postgres.get_conn()

    try:
        dataframe = pd.read_sql_query(
            sql=sql,
            con=connection,
            params=params,
        )
    finally:
        connection.close()

    if dataframe.empty:
        message = f"Upper cursor existed for {schema}.{table}, but no rows were read."
        logger.info(message)
        raise AirflowSkipException(message)

    object_keys = write_dataframe_to_minio(
        dataframe=dataframe,
        table=table,
        partition_column=partition_column,
        partition_name=partition_name,
        previous_cursor=previous_cursor,
        upper_cursor=upper_cursor,
    )

    return {
        "table": f"{schema}.{table}",
        "rows": len(dataframe),
        "chunks": 1,
        "previous_cursor": previous_cursor,
        "new_cursor": upper_cursor,
        "object_keys": object_keys,
    }


def extract_non_partitioned_table(
    postgres: PostgresHook,
    sql: str,
    params: dict[str, str],
    schema: str,
    table: str,
    cursor_column: str,
    previous_cursor: str,
    upper_cursor: str,
) -> dict[str, Any]:
    object_keys: list[str] = []
    total_rows = 0
    chunk_count = 0
    chunk_previous_cursor = previous_cursor

    connection = postgres.get_conn()

    try:
        chunks = pd.read_sql_query(
            sql=sql,
            con=connection,
            params=params,
            chunksize=EXTRACT_CHUNK_SIZE,
        )

        for dataframe_chunk in chunks:
            if dataframe_chunk.empty:
                continue

            chunk_count += 1
            total_rows += len(dataframe_chunk)

            chunk_upper_cursor = str(dataframe_chunk[cursor_column].max())

            chunk_object_keys = write_dataframe_to_minio(
                dataframe=dataframe_chunk,
                table=table,
                partition_column=None,
                partition_name=None,
                previous_cursor=chunk_previous_cursor,
                upper_cursor=chunk_upper_cursor,
            )

            object_keys.extend(chunk_object_keys)
            chunk_previous_cursor = chunk_upper_cursor

    finally:
        connection.close()

    if total_rows == 0:
        message = f"Upper cursor existed for {schema}.{table}, but no rows were read."
        logger.info(message)
        raise AirflowSkipException(message)

    return {
        "table": f"{schema}.{table}",
        "rows": total_rows,
        "chunks": chunk_count,
        "previous_cursor": previous_cursor,
        "new_cursor": upper_cursor,
        "object_keys": object_keys,
    }


def get_upper_cursor(
    postgres: PostgresHook,
    schema: str,
    table: str,
    cursor_column: str,
    previous_cursor: str,
) -> str | None:
    sql = f"""
        SELECT MAX({cursor_column})
        FROM {schema}.{table}
        WHERE {cursor_column} > %(last_updated_at)s::BIGINT
    """

    row = postgres.get_first(
        sql,
        parameters={
            "last_updated_at": previous_cursor,
        },
    )

    if row is None or row[0] is None:
        return None

    return str(row[0])
