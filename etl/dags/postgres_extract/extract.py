"""
extract.py
PostgreSQL table extraction logic for the MinIO staging layer.

This module supports full extraction for small tables and chunked extraction
for large tables. It manages incremental cursor ranges, reads source rows from
PostgreSQL, delegates Parquet writes to the storage layer, and advances the
cursor only after all uploads succeed.
"""

from __future__ import annotations

import logging
from contextlib import closing
from typing import Any
from uuid import uuid4

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook

from postgres_extract.config import (
    MINIO_CONN_ID,
    POSTGRES_CONN_ID,
    POSTGRES_SCHEMA,
)
from postgres_extract.cursors import get_cursor, set_cursor
from postgres_extract.parquet import write_dataframe_to_minio

logger = logging.getLogger(__name__)


def _get_high_watermark(
    connection: Any,
    table_name: str,
    cursor_column: str,
) -> int:
    """
    Return the highest source cursor value that is older than the safety lag.
    """
    query = f"""
        SELECT COALESCE(MAX("{cursor_column}"), 0)
        FROM "{POSTGRES_SCHEMA}"."{table_name}"
        WHERE "{cursor_column}" <=
            EXTRACT(EPOCH FROM NOW() - INTERVAL '30 seconds')::bigint
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchone()

    if result is None:
        raise RuntimeError(
            f"Could not determine high watermark for {POSTGRES_SCHEMA}.{table_name}."
        )

    return int(result[0])


def _extract_full_result(
    connection: Any,
    query: str,
    query_parameters: tuple,
    s3_hook: S3Hook,
    table_name: str,
    cursor_from_ts: int | None,
    cursor_from_id: int,
    cursor_to: int,
    partition_config: dict[str, str] | None,
) -> tuple[int, int, int, int]:
    """
    Extract a small result set in memory and write it to MinIO.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            query,
            query_parameters,
        )

        rows = cursor.fetchall()

        if cursor.description is None:
            raise RuntimeError(
                "Postgres returned no column metadata for "
                f"{POSTGRES_SCHEMA}.{table_name}."
            )

        column_names = [description[0] for description in cursor.description]

    if not rows:
        return 0, 0, 0, cursor_from_id

    dataframe = pd.DataFrame(
        rows,
        columns=column_names,
    )

    last_row_id = int(dataframe["id"].iloc[-1])

    uploaded_objects = write_dataframe_to_minio(
        s3_hook=s3_hook,
        table_name=table_name,
        dataframe=dataframe,
        cursor_from=cursor_from_ts,
        cursor_to=cursor_to,
        partition_config=partition_config,
        part_number=None,
    )

    total_rows = len(dataframe)

    logger.info(
        "Processed full result: table=%s rows=%s uploaded_objects=%s",
        table_name,
        total_rows,
        uploaded_objects,
    )

    return total_rows, uploaded_objects, 1, last_row_id


def _extract_chunked_result(
    connection: Any,
    query: str,
    query_parameters: tuple,
    s3_hook: S3Hook,
    table_name: str,
    cursor_from_ts: int | None,
    cursor_from_id: int,
    cursor_to: int,
    chunk_size: int,
    partition_config: dict[str, str] | None,
) -> tuple[int, int, int, int]:
    """
    Extract a large result set in chunks and write each chunk to MinIO.
    """
    total_rows = 0
    uploaded_objects = 0
    part_number = 0
    last_row_id = cursor_from_id

    server_cursor_name = f"extract_{table_name}_{uuid4().hex}"

    with connection.cursor(name=server_cursor_name) as cursor:
        if hasattr(cursor, "itersize"):
            cursor.itersize = chunk_size

        cursor.execute(
            query,
            query_parameters,
        )

        # For a server-side cursor, fetch the first chunk before reading
        # cursor.description.
        rows = cursor.fetchmany(chunk_size)

        if not rows:
            return 0, 0, 0, cursor_from_id

        if cursor.description is None:
            raise RuntimeError(
                "Postgres returned no column metadata for "
                f"{POSTGRES_SCHEMA}.{table_name} "
                "after fetching the first chunk."
            )

        column_names = [description[0] for description in cursor.description]

        while rows:
            dataframe = pd.DataFrame(
                rows,
                columns=column_names,
            )

            current_chunk_rows = len(dataframe)
            last_row_id = int(dataframe["id"].iloc[-1])

            uploaded_objects += write_dataframe_to_minio(
                s3_hook=s3_hook,
                table_name=table_name,
                dataframe=dataframe,
                cursor_from=cursor_from_ts,
                cursor_to=cursor_to,
                partition_config=partition_config,
                part_number=part_number,
            )

            logger.info(
                "Processed chunk: table=%s part=%05d rows=%s uploaded_objects=%s",
                table_name,
                part_number,
                current_chunk_rows,
                uploaded_objects,
            )

            total_rows += current_chunk_rows
            part_number += 1

            del dataframe
            del rows

            rows = cursor.fetchmany(chunk_size)

    return total_rows, uploaded_objects, part_number, last_row_id


def extract_table_to_minio(
    table_config: dict[str, Any],
) -> None:
    """
    Incrementally extract one configured PostgreSQL table to MinIO.
    """
    table_name = table_config["table"]
    cursor_column = table_config["cursor_column"]
    tie_breaker_column = table_config.get("tie_breaker_column", "id")
    partition_config = table_config.get("partition")

    extract_strategy = table_config.get(
        "extract_strategy",
        "full",
    )

    if extract_strategy not in {
        "full",
        "chunked",
    }:
        raise ValueError(
            f"Unsupported extract strategy "
            f"{extract_strategy!r} for table {table_name!r}."
        )

    cursor_from_ts, cursor_from_id = get_cursor(table_name)

    postgres_hook = PostgresHook(
        postgres_conn_id=POSTGRES_CONN_ID,
    )
    s3_hook = S3Hook(
        aws_conn_id=MINIO_CONN_ID,
    )

    with closing(postgres_hook.get_conn()) as connection:
        cursor_to = _get_high_watermark(
            connection=connection,
            table_name=table_name,
            cursor_column=cursor_column,
        )

        logger.info(
            "Starting extraction: table=%s strategy=%s "
            "cursor_from_ts=%s cursor_from_id=%s cursor_to=%s",
            table_name,
            extract_strategy,
            cursor_from_ts,
            cursor_from_id,
            cursor_to,
        )

        if cursor_from_ts is not None and cursor_to <= cursor_from_ts:
            raise AirflowSkipException(
                "No new or changed rows found for "
                f"{POSTGRES_SCHEMA}.{table_name}. "
                f"Current cursor is ({cursor_from_ts}, {cursor_from_id})."
            )

        # Use a keyset / row-value comparison so that rows sharing the same
        # cursor_column value are never skipped.
        if cursor_from_ts is None:
            query = f"""
                SELECT *
                FROM "{POSTGRES_SCHEMA}"."{table_name}"
                WHERE "{cursor_column}" <= %s
                ORDER BY
                    "{cursor_column}" ASC,
                    "{tie_breaker_column}" ASC
            """
            query_parameters = (cursor_to,)
        else:
            query = f"""
                SELECT *
                FROM "{POSTGRES_SCHEMA}"."{table_name}"
                WHERE ("{cursor_column}", "{tie_breaker_column}") > (%s, %s)
                  AND "{cursor_column}" <= %s
                ORDER BY
                    "{cursor_column}" ASC,
                    "{tie_breaker_column}" ASC
            """
            query_parameters = (cursor_from_ts, cursor_from_id, cursor_to)

        if extract_strategy == "full":
            (
                total_rows,
                uploaded_objects,
                processed_batches,
                last_row_id,
            ) = _extract_full_result(
                connection=connection,
                query=query,
                query_parameters=query_parameters,
                s3_hook=s3_hook,
                table_name=table_name,
                cursor_from_ts=cursor_from_ts,
                cursor_from_id=cursor_from_id,
                cursor_to=cursor_to,
                partition_config=partition_config,
            )

        else:
            chunk_size = int(table_config["chunk_size"])

            if chunk_size <= 0:
                raise ValueError(
                    f"Chunk size for table {table_name!r} must be greater than zero."
                )

            (
                total_rows,
                uploaded_objects,
                processed_batches,
                last_row_id,
            ) = _extract_chunked_result(
                connection=connection,
                query=query,
                query_parameters=query_parameters,
                s3_hook=s3_hook,
                table_name=table_name,
                cursor_from_ts=cursor_from_ts,
                cursor_from_id=cursor_from_id,
                cursor_to=cursor_to,
                chunk_size=chunk_size,
                partition_config=partition_config,
            )

    if total_rows == 0:
        raise AirflowSkipException(
            "No rows were returned for "
            f"{POSTGRES_SCHEMA}.{table_name} "
            f"in cursor range ({cursor_from_ts}, {cursor_from_id}) → {cursor_to}."
        )

    # Advance the composite cursor only after all Parquet uploads have succeeded.
    set_cursor(
        table_name,
        cursor_to,
        last_row_id,
    )

    logger.info(
        "Extraction completed: table=%s strategy=%s "
        "cursor_from_ts=%s cursor_from_id=%s cursor_to=%s last_row_id=%s "
        "rows=%s batches=%s uploaded_objects=%s",
        table_name,
        extract_strategy,
        cursor_from_ts,
        cursor_from_id,
        cursor_to,
        last_row_id,
        total_rows,
        processed_batches,
        uploaded_objects,
    )
