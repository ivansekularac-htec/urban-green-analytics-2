from __future__ import annotations

from airflow.exceptions import AirflowSkipException
from airflow.providers.postgres.hooks.postgres import PostgresHook
from postgres_extract.cursor import (
    CURSOR_COLUMN,
    POSTGRES_CONN_ID,
    PRIMARY_KEY,
    SCHEMA,
    _high_watermark,
    _run_cutoff,
    get_cursor,
)

FETCH_MANY = 50000


def _select_query(table: str, has_cursor: bool) -> str:
    if has_cursor:
        return f"""
            SELECT *
            FROM {SCHEMA}.{table}
            WHERE ({CURSOR_COLUMN} > %s OR ({CURSOR_COLUMN} = %s AND {PRIMARY_KEY} > %s))
              AND {CURSOR_COLUMN} <= %s
            ORDER BY {CURSOR_COLUMN} ASC, {PRIMARY_KEY} ASC
        """
    return f"""
        SELECT *
        FROM {SCHEMA}.{table}
        WHERE {CURSOR_COLUMN} <= %s
        ORDER BY {CURSOR_COLUMN} ASC, {PRIMARY_KEY} ASC
    """


def _build_query_parameters(
    current_cursor: dict[str, str] | None,
    run_cutoff: int,
) -> tuple[str, ...] | tuple[int]:
    if current_cursor and current_cursor.get("updated_at") is not None:
        return (
            current_cursor["updated_at"],
            current_cursor["updated_at"],
            current_cursor["id"] or "0",
            run_cutoff,
        )
    return (run_cutoff,)


def _fetch_rows(cursor, table: str) -> list[tuple]:
    if table == "harvests":
        rows = []
        while True:
            batch = cursor.fetchmany(FETCH_MANY)
            if not batch:
                break
            rows.extend(batch)
        return rows
    return cursor.fetchall()


def extract_table(
    table: str,
) -> tuple[list[str], list[tuple], dict[str, str]]:
    current_cursor = get_cursor(table)
    has_cursor = (
        current_cursor is not None and current_cursor.get("updated_at") is not None
    )
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    run_cutoff = _run_cutoff(hook)
    high_watermark = _high_watermark(hook, table, current_cursor, run_cutoff)

    if high_watermark is None:
        raise AirflowSkipException("No new rows to extract")

    query = _select_query(table, has_cursor)
    parameters = _build_query_parameters(current_cursor, run_cutoff)

    with hook.get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, parameters)
            columns = [desc[0] for desc in cursor.description]
            rows = _fetch_rows(cursor, table)

    if not rows:
        raise AirflowSkipException("No rows found for window")

    return columns, rows, high_watermark
