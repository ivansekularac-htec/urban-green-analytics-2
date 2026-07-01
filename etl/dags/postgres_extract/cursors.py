"""
cursors.py
Airflow Variable helpers for PostgreSQL extraction cursors.

This module stores and retrieves the last successfully processed cursor value
for each source table.
"""

from __future__ import annotations

from airflow.sdk import Variable


def cursor_variable_name(table_name: str) -> str:
    """
    Return the Airflow Variable name used for a table cursor.
    """
    return f"postgres_extract_cursor__{table_name}"


def get_cursor(table_name: str) -> str | None:
    """
    Return the last successfully processed cursor for a table, or None if
    the table has never been extracted.
    """
    return Variable.get(cursor_variable_name(table_name), default=None)


def set_cursor(table_name: str, cursor_value: str) -> None:
    """
    Store the last successfully processed cursor for a table.
    """
    Variable.set(cursor_variable_name(table_name), cursor_value)
