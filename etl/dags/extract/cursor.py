import json

from airflow.sdk import Variable


def variable_name(table_name: str) -> str:
    """
    Return the Airflow Variable name used to store the extraction cursor.

    Args:
        table_name: Name of the source table.

    Returns:
        The Airflow Variable key for the table's cursor.
    """

    return f"extract.{table_name}.cursor"


def get_cursor(table_config: dict) -> str:
    """
    Retrieve the last successfully processed cursor for a table.

    If the cursor variable does not exist, returns "0" so the initial
    extraction processes all available records.

    Args:
        table_config:
            Table configuration containing the table name and cursor column.

    Returns:
        The stored cursor value.
    """
    table_name = table_config["name"]
    cursor_column = table_config["cursor_column"]

    try:
        value = Variable.get(variable_name(table_name))
    except Exception:
        return "0"

    try:
        data = json.loads(value)
        return str(data.get(cursor_column, "0"))
    except (TypeError, ValueError):
        return "0"


def update_cursor(
    table_config: dict,
    cursor: str,
) -> None:
    """
    Store the latest successfully processed cursor for a table.

    Args:
        table_config:
            Table configuration containing the table name and cursor column.
        cursor:
            Cursor value to persist.
    """
    table_name = table_config["name"]
    cursor_column = table_config["cursor_column"]

    cursor_value = cursor

    Variable.set(
        variable_name(table_name),
        json.dumps(
            {
                cursor_column: cursor_value,
            }
        ),
    )
