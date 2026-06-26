from __future__ import annotations

import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook

from extract_common.settings import EXTRACT_SAFETY_LAG_SECONDS


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
        SELECT {cursor_column}, {primary_key}
        FROM {schema}.{table}
        WHERE (
            {cursor_column} > %(last_updated_at)s
            OR ({cursor_column} = %(last_updated_at)s AND {primary_key} > %(last_id)s)
        )
        AND {cursor_column} <= %(run_cutoff)s
        ORDER BY {cursor_column} DESC, {primary_key} DESC
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
    sql = f"""
        SELECT *
        FROM {schema}.{table}
        WHERE (
            {cursor_column} > %(last_updated_at)s
            OR ({cursor_column} = %(last_updated_at)s AND {primary_key} > %(last_id)s)
        )
        AND (
            {cursor_column} < %(upper_updated_at)s
            OR ({cursor_column} = %(upper_updated_at)s AND {primary_key} <= %(upper_id)s)
        )
        ORDER BY {cursor_column}, {primary_key}
    """

    params = {
        "last_updated_at": previous_cursor["updated_at"],
        "last_id": previous_cursor["id"],
        "upper_updated_at": upper_cursor["updated_at"],
        "upper_id": upper_cursor["id"],
    }

    connection = postgres.get_conn()

    try:
        return pd.read_sql_query(sql=sql, con=connection, params=params)
    finally:
        connection.close()