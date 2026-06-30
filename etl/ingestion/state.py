import json
import logging

from airflow.models import Variable

logger = logging.getLogger(__name__)


def get_cursor(table):
    """
    Retrieves the last successfully processed ingestion cursor
    for a given table from Airflow Variables.

    This cursor enables incremental extraction from Postgres.

    Cursor format:
        {
            "updated_at": int,
            "id": int
        }

    Args:
        table (str): Table name

    Returns:
        tuple[int, int]:
            (updated_at, id)

    Behavior:
        - Returns (0, 0) if no cursor exists (full backfill)
        - Returns (0, 0) if cursor is corrupted (safe recovery mode)
        - Guarantees ingestion never breaks due to bad state
    """

    cursor_raw = Variable.get(f"{table}_cursor", default_var=None)

    if not cursor_raw:
        return 0, 0

    try:
        cursor = json.loads(cursor_raw)

        return (
            int(cursor.get("updated_at", 0)),
            int(cursor.get("id", 0)),
        )

    except (json.JSONDecodeError, TypeError, ValueError):
        logger.warning(
            f"Invalid cursor for table '{table}'. Resetting cursor to (0, 0)."
        )
        return 0, 0


def set_cursor(table, cursor_column, row):
    """
    Persists the ingestion cursor after a successful extraction run.

    IMPORTANT:
        Cursor is only updated after:
        - successful Postgres extraction
        - successful Parquet write
        - successful MinIO upload

    This guarantees idempotency under retries.

    Args:
        table (str): Table name
        cursor_column (str): Column used for incremental tracking
        row (dict-like): Last row from extracted dataset

    Returns:
        dict:
            Updated cursor state
    """

    new_cursor = {
        "updated_at": int(row[cursor_column]),
        "id": int(row["id"]),
    }

    Variable.set(f"{table}_cursor", json.dumps(new_cursor))

    return new_cursor
