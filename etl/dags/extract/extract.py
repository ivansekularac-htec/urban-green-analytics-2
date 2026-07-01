from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import uuid4

from airflow.providers.postgres.hooks.postgres import PostgresHook
from extract.utils import (
    POSTGRES_CONN_ID,
    SCHEMA,
)


def _build_extract_sql(
    schema: str,
    table_name: str,
    cursor_column: str,
) -> str:
    """Build extraction SQL with cursor pagination."""
    return f'''
        SELECT *
        FROM "{schema}"."{table_name}"
        WHERE "{cursor_column}" > %s AND "{cursor_column}" <= %s
    '''


def _stream_query(
    conn,
    sql: str,
    params: tuple,
    batch_size: int,
    table_name: str,
) -> Iterator[tuple[list[tuple], list[str]]]:
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
    cursor: str | None,
    cursor_column: str,
    batch_size: int = 200000,
) -> Iterator[tuple[list[tuple], list[str]]]:
    """
    Stream incremental data from a Postgres table in batches.

    This function is designed for large-scale ETL pipelines where loading
    entire tables into memory is not safe or efficient.

    It uses a cursor-based incremental approach and yields results in chunks
    suitable for streaming into Parquet (e.g., via PyArrow).

    Args:
    table_name (str):
        Name of the table inside the configured schema.

    cursor (str | None):
        Last successfully processed cursor value.

    cursor_column (str):
        Column used for incremental cursor pagination.

    batch_size (int, optional):
        Number of rows per batch. Default is 200000.

    Yields:
        tuple[list[tuple], list[str]]:
            A batch of rows together with the corresponding column names.
    """

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    conn = None
    try:
        conn = hook.get_conn()

        sql = _build_extract_sql(
            SCHEMA,
            table_name,
            cursor_column,
        )

        cursor = cursor or "0"

        yield from _stream_query(
            conn,
            sql,
            (
                int(cursor),
                int(datetime.now(timezone.utc).timestamp()),
            ),
            batch_size,
            table_name,
        )

    except Exception as exc:
        raise RuntimeError(f"Failed to extract '{SCHEMA}.{table_name}': {exc}") from exc

    finally:
        if conn is not None:
            conn.close()
