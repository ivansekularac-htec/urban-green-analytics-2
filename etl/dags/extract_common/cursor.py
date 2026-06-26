from __future__ import annotations

from airflow.sdk import Variable

from extract_common.settings import DEFAULT_CURSOR


def cursor_variable_key(schema: str, table: str) -> str:
    return f"extract_cursor_{schema}_{table}"


def get_cursor(cursor_key: str) -> dict[str, int]:
    try:
        cursor = Variable.get(cursor_key, default=DEFAULT_CURSOR, deserialize_json=True)
    except TypeError:
        # Compatibility fallback for older Airflow Variable API signatures.
        cursor = Variable.get(cursor_key, default_var=DEFAULT_CURSOR, deserialize_json=True)

    if not isinstance(cursor, dict):
        raise ValueError(f"Cursor variable {cursor_key} must be a JSON object.")

    try:
        normalized_cursor = {
            "updated_at": int(cursor.get("updated_at", 0)),
            "id": int(cursor.get("id", 0)),
        }
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Cursor variable {cursor_key} has invalid values: {cursor}") from exc

    if normalized_cursor["updated_at"] < 0 or normalized_cursor["id"] < 0:
        raise ValueError(f"Cursor variable {cursor_key} cannot contain negative values: {cursor}")

    return normalized_cursor


def set_cursor(cursor_key: str, cursor: dict[str, int]) -> None:
    Variable.set(cursor_key, cursor, serialize_json=True)