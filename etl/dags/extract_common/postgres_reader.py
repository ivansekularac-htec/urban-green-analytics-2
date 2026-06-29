from __future__ import annotations

import os
import re
from collections.abc import Iterator
from typing import Final

import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook

from extract_common.settings import EXTRACT_SAFETY_LAG_SECONDS

DEFAULT_EXTRACT_CHUNK_SIZE: Final[int] = int(os.getenv("EXTRACT_CHUNK_SIZE", "50000"))

_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def assert_table_shape(
    postgres: PostgresHook,
    schema: str,
    table: str,
    primary_key: str,
    cursor_column: str,
    partition_column: str | None,
) -> None:
    expected_columns = {primary_key, cursor_column}

    if partition_column is not None:
        expected_columns.add(partition_column)

    rows = postgres.get_records(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %(schema)s
          AND table_name = %(table)s
          AND column_name = ANY(%(expected_columns)s)
        """,
        parameters={
            "schema": schema,
            "table": table,
            "expected_columns": list(expected_columns),
        },
    )

    found_columns = {row[0] for row in rows}
    missing_columns = sorted(expected_columns - found_columns)

    if missing_columns:
        raise ValueError(
            f"Table {schema}.{table} is missing required extract columns: {missing_columns}"
        )


def get_run_cutoff(postgres: PostgresHook) -> int:
    row = postgres.get_first(
        """
        SELECT (EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT - %(safety_lag)s)
            AS run_cutoff
        """,
        parameters={"safety_lag": EXTRACT_SAFETY_LAG_SECONDS},
    )

    if row is None:
        raise ValueError("Could not calculate extract run cutoff from Postgres.")

    return max(int(row[0]), 0)


def get_upper_cursor(
    postgres: PostgresHook,
    schema: str,
    table: str,
    cursor_column: str,
    primary_key: str,
    previous_cursor: dict[str, int],
    run_cutoff: int,
) -> dict[str, int] | None:
    sql = f"""
        SELECT {_safe_identifier(cursor_column, "cursor_column")},
               {_safe_identifier(primary_key, "primary_key")}
        FROM {_safe_identifier(schema, "schema")}.{_safe_identifier(table, "table")}
        WHERE (
            {_safe_identifier(cursor_column, "cursor_column")} > %(last_updated_at)s
            OR (
                {_safe_identifier(cursor_column, "cursor_column")} = %(last_updated_at)s
                AND {_safe_identifier(primary_key, "primary_key")} > %(last_id)s
            )
        )
        AND {_safe_identifier(cursor_column, "cursor_column")} <= %(run_cutoff)s
        ORDER BY {_safe_identifier(cursor_column, "cursor_column")} DESC,
                 {_safe_identifier(primary_key, "primary_key")} DESC
        LIMIT 1
    """

    row = postgres.get_first(
        sql,
        parameters={
            "last_updated_at": previous_cursor["updated_at"],
            "last_id": previous_cursor["id"],
            "run_cutoff": run_cutoff,
        },
    )

    if row is None:
        return None

    return {"updated_at": int(row[0]), "id": int(row[1])}


def read_changed_rows(
    postgres: PostgresHook,
    schema: str,
    table: str,
    cursor_column: str,
    primary_key: str,
    previous_cursor: dict[str, int],
    upper_cursor: dict[str, int],
) -> pd.DataFrame:
    """Read changed rows into a single DataFrame.

    This function is kept for small tables and for backward compatibility with the
    current extractor implementation.

    For large tables such as harvests, use read_changed_rows_in_chunks instead.
    """
    sql = _build_changed_rows_query(
        schema=schema,
        table=table,
        cursor_column=cursor_column,
        primary_key=primary_key,
    )

    params = _build_changed_rows_params(
        previous_cursor=previous_cursor,
        upper_cursor=upper_cursor,
    )

    connection = postgres.get_conn()

    try:
        return pd.read_sql_query(sql=sql, con=connection, params=params)
    finally:
        connection.close()


def read_changed_rows_in_chunks(
    postgres: PostgresHook,
    schema: str,
    table: str,
    cursor_column: str,
    primary_key: str,
    previous_cursor: dict[str, int],
    upper_cursor: dict[str, int],
    chunk_size: int = DEFAULT_EXTRACT_CHUNK_SIZE,
) -> Iterator[pd.DataFrame]:
    """Read changed rows from Postgres in chunks.

    This avoids loading the full result set into Airflow worker memory at once.
    It is the safer option for large initial extracts such as harvests.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    sql = _build_changed_rows_query(
        schema=schema,
        table=table,
        cursor_column=cursor_column,
        primary_key=primary_key,
    )

    params = _build_changed_rows_params(
        previous_cursor=previous_cursor,
        upper_cursor=upper_cursor,
    )

    connection = postgres.get_conn()

    try:
        yield from pd.read_sql_query(
            sql=sql,
            con=connection,
            params=params,
            chunksize=chunk_size,
        )
    finally:
        connection.close()


def _build_changed_rows_query(
    schema: str,
    table: str,
    cursor_column: str,
    primary_key: str,
) -> str:
    safe_schema = _safe_identifier(schema, "schema")
    safe_table = _safe_identifier(table, "table")
    safe_cursor_column = _safe_identifier(cursor_column, "cursor_column")
    safe_primary_key = _safe_identifier(primary_key, "primary_key")

    return f"""
        SELECT *
        FROM {safe_schema}.{safe_table}
        WHERE (
            {safe_cursor_column} > %(last_updated_at)s
            OR ({safe_cursor_column} = %(last_updated_at)s AND {safe_primary_key} > %(last_id)s)
        )
        AND (
            {safe_cursor_column} < %(upper_updated_at)s
            OR ({safe_cursor_column} = %(upper_updated_at)s AND {safe_primary_key} <= %(upper_id)s)
        )
        ORDER BY {safe_cursor_column}, {safe_primary_key}
    """


def _build_changed_rows_params(
    previous_cursor: dict[str, int],
    upper_cursor: dict[str, int],
) -> dict[str, int]:
    return {
        "last_updated_at": previous_cursor["updated_at"],
        "last_id": previous_cursor["id"],
        "upper_updated_at": upper_cursor["updated_at"],
        "upper_id": upper_cursor["id"],
    }


def _safe_identifier(value: str, label: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid SQL identifier for {label}: {value}")

    return value
