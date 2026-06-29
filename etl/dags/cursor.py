import json

from airflow.sdk import Variable


def variable_name(table: str) -> str:
    """
    Return the Airflow Variable name used to store the extraction cursor.

    Args:
        table: Name of the source table.

    Returns:
        The Airflow Variable key for the table's cursor.
    """

    return f"extract.{table}.cursor"


def get_cursor(table: str) -> int:
    """
    Retrieve the last successfully processed cursor for a table.

    If the cursor variable does not exist, returns ``0`` so the initial
    extraction processes all available records.

    Args:
        table: Name of the source table.

    Returns:
        The last processed cursor value, or ``0`` if no cursor exists.
    """

    try:
        value = Variable.get(variable_name(table))
    except Exception:
        return (0, 0)

    try:
        data = json.loads(value)
        return (int(data["updated_at"]), int(data["id"]))
    except (TypeError, ValueError):
        return (0, 0)


def update_cursor(table: str, cursor: int):
    """
    Store the latest successfully processed cursor for a table.

    Args:
        table: Name of the source table.
        cursor: Cursor value to persist.
    """

    if not cursor:
        return

    updated_at, id_value = cursor

    Variable.set(
        variable_name(table),
        json.dumps(
            {
                "updated_at": int(updated_at),
                "id": int(id_value),
            }
        ),
    )


def reset_cursor(table: str):
    """
    Delete the stored cursor for a table.

    This causes the next extraction to start from the initial cursor
    value (``0``).

    Args:
        table: Name of the source table.
    """

    Variable.delete(variable_name(table))
