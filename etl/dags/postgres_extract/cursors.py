"""
cursors.py
Airflow Variable helpers for PostgreSQL extraction cursors.

This module stores and retrieves the last successfully processed cursor value
for each source table.
"""

from __future__ import annotations

from airflow.sdk import Variable

_CURSOR_SEPARATOR = "|"


def cursor_variable_name(table_name: str) -> str:
    """
    Return the Airflow Variable name used for a table cursor.
    """
    return f"postgres_extract_cursor__{table_name}"


def get_cursor(table_name: str) -> tuple[int | None, int]:
    """
    Return the last successfully processed cursor value for a table.
    """
    value = Variable.get(cursor_variable_name(table_name), default=None)

    if value is None:
        return None, 0

    ts_str, id_str = value.split(_CURSOR_SEPARATOR, 1)
    return int(ts_str), int(id_str)


def set_cursor(table_name: str, timestamp: int, row_id: int) -> None:
    """
    Store the last successfully processed cursor value for a table.
    """
    value = f"{timestamp}{_CURSOR_SEPARATOR}{row_id}"
    Variable.set(cursor_variable_name(table_name), value)
