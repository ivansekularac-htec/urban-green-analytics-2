import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator, List, Optional, Tuple
from uuid import uuid4

from airflow.providers.postgres.hooks.postgres import PostgresHook
from extract.utils import (
    POSTGRES_CONN_ID,
    SCHEMA,
)

logger = logging.getLogger(__name__)


def _get_table_columns(conn, schema: str, table_name: str) -> List[str]:
    """Fetch column names from Postgres information schema."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema, table_name),
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()


def _validate_columns(
    columns: List[str],
    cursor_column: str,
    id_column: str,
    table_name: str,
):
    """Ensure required columns exist in table schema."""
    if cursor_column not in columns:
        raise ValueError(f"Cursor column '{cursor_column}' not found in '{table_name}'")
    if id_column not in columns:
        raise ValueError(f"Id column '{id_column}' not found in '{table_name}'")


def _build_extract_sql(
    schema: str,
    table_name: str,
    cursor_column: str,
    id_column: str,
) -> str:
    """Build extraction SQL with cursor pagination."""
    return f'''
        SELECT *
        FROM "{schema}"."{table_name}"
        WHERE ("{cursor_column}", "{id_column}") > (%s, %s)
          AND "{cursor_column}" <= %s
        ORDER BY "{cursor_column}" ASC, "{id_column}" ASC
    '''


def _get_upper_bound() -> int:
    """Return safe upper bound timestamp (30s lag for consistency)."""
    return int((datetime.now(timezone.utc) - timedelta(seconds=30)).timestamp())


def _stream_query(
    conn,
    sql: str,
    params: tuple,
    batch_size: int,
    table_name: str,
) -> Iterator[Tuple[List[tuple], List[str]]]:
    """Stream query results using server-side cursor."""
    cur = conn.cursor(name=f"extract_{table_name}_{uuid4().hex}")
    cur.itersize = batch_size
    cur.execute(sql, params)

    columns = None

    try:
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break

            if columns is None:
                columns = [desc[0] for desc in cur.description]

            yield rows, columns
    finally:
        cur.close()


def extract_table(
    table_name: str,
    cursor: Optional[Tuple[Any, Any]],
    cursor_column: str,
    id_column: str = "id",
    batch_size: int = 10000,
) -> Iterator[Tuple[List[tuple], List[str]]]:
    """
    Stream incremental data from a Postgres table in batches.

    This function is designed for large-scale ETL pipelines where loading
    entire tables into memory is not safe or efficient.

    It uses a cursor-based incremental approach and yields results in chunks
    suitable for streaming into Parquet (e.g., via PyArrow).

    Args:
        table_name (str):
            Name of the table inside the configured schema.

        cursor (int, int):
            Last successfully processed cursor value (typically epoch timestamp
            stored in Airflow Variables).

         cursor_column:

        batch_size (int, optional):
            Number of rows to fetch per iteration. Default is 10000.

    Yields:
        Iterator[Tuple[List[tuple], List[str]]]:
            A tuple containing:
                - rows (list of tuples): batch of database rows
                - columns (list of str): column names of the table
    """

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    conn = None
    try:
        conn = hook.get_conn()

        columns = _get_table_columns(conn, SCHEMA, table_name)

        _validate_columns(columns, cursor_column, id_column, table_name)

        sql = _build_extract_sql(
            SCHEMA,
            table_name,
            cursor_column,
            id_column,
        )

        cursor = cursor or (0, 0)
        upper_bound = _get_upper_bound()

        yield from _stream_query(
            conn,
            sql,
            (cursor[0], cursor[1], upper_bound),
            batch_size,
            table_name,
        )

    except Exception as exc:
        raise RuntimeError(f"Failed to extract '{SCHEMA}.{table_name}': {exc}") from exc

    finally:
        if conn is not None:
            conn.close()
