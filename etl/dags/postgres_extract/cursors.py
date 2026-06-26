from __future__ import annotations

from airflow.sdk import Variable


def cursor_variable_name(table_name: str) -> str:
    return f"postgres_extract_cursor__{table_name}"


def get_cursor(table_name: str) -> int:
    variable_name = cursor_variable_name(table_name)
    value = Variable.get(variable_name, default=None)

    if value is None:
        Variable.set(variable_name, "0000000000")
        return 0

    return int(value)


def set_cursor(table_name: str, value: int) -> None:
    Variable.set(cursor_variable_name(table_name), str(value))
