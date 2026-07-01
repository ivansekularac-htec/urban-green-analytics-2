from __future__ import annotations

from airflow.sdk import Variable

DEFAULT_CURSOR = "0"


def cursor_key(schema: str, table: str) -> str:
    return f"extract_cursor_{schema}_{table}"


def get_cursor(key: str) -> str:
    cursor = Variable.get(
        key,
        default=DEFAULT_CURSOR,
        deserialize_json=True,
    )

    return str(cursor)


def set_cursor(key: str, cursor: str) -> None:
    Variable.set(key, str(cursor), serialize_json=True)
