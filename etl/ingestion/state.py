import json

from airflow.models import Variable


def get_cursor(table):
    """
    Retrieves the last successfully processed ingestion cursor
    for a given table from Airflow Variables.

    The cursor is used to perform incremental extraction from Postgres.

    Cursor format:
        {
            "updated_at": int,
            "id": int
        }

    Args:
        table (str):
            Name of the table whose cursor should be retrieved.

    Returns:
        tuple:
            (updated_at, id)
            - updated_at (int): timestamp of last processed record
            - id (int): last processed row id (used for deterministic ordering)

    Behavior:
        - If no cursor exists, returns (0, 0) for full backfill
        - If cursor is corrupted or invalid, safely resets to (0, 0)
        - Ensures ingestion can always recover without manual intervention
    """

    cursor_raw = Variable.get(f"{table}_cursor", default_var=None)

    if not cursor_raw:
        return 0, 0

    try:
        cursor = json.loads(cursor_raw)

        updated_at = int(cursor.get("updated_at", 0))
        row_id = int(cursor.get("id", 0))

        return updated_at, row_id

    except Exception:
        # Safe fallback: allows full reprocessing on corruption
        return 0, 0


def set_cursor(table, cursor_column, row):
    """
    Persists the ingestion cursor after successful extraction.

    The cursor is advanced only after data is successfully:
    - extracted from Postgres
    - written to Parquet
    - uploaded to object storage (MinIO)

    Args:
        table (str):
            Table name being processed.

        cursor_column (str):
            Column used as primary incremental marker (e.g. updated_at).

        row (dict-like):
            Last row from the extracted dataset, used to derive new cursor values.

    Returns:
        dict:
            Newly stored cursor in the format:
            {
                "updated_at": int,
                "id": int
            }

    Notes:
        - This ensures idempotent ingestion under Airflow retries
        - Cursor represents the *last successfully committed record*
    """

    new_cursor = {
        "updated_at": int(row[cursor_column]),
        "id": int(row["id"]),
    }

    Variable.set(f"{table}_cursor", json.dumps(new_cursor))

    return new_cursor
