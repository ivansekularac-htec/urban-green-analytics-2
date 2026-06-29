import logging
from typing import Iterator, List, Tuple

from airflow.providers.postgres.hooks.postgres import PostgresHook
from config import (
    POSTGRES_CONN_ID,
    SCHEMA,
)

logger = logging.getLogger(__name__)


def extract_table(
    table_name: str,
    cursor: int,
    cursor_column: str,
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

        cursor (int):
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

    try:
        conn = hook.get_conn()
        cur = conn.cursor()

        column_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        cur.execute(column_query, (SCHEMA, table_name))
        available_columns = [row[0] for row in cur.fetchall()]

        if cursor_column not in available_columns:
            raise ValueError(
                f"Cursor column '{cursor_column}' not found in table '{table_name}'"
            )

        select_list = ", ".join(f'"{column}"' for column in available_columns)
        sql = f"""
            SELECT {select_list}
            FROM {SCHEMA}.{table_name}
            WHERE {cursor_column} > %s
            ORDER BY {cursor_column} ASC
        """

        logger.info(
            "Extracting table '%s' from schema '%s' using cursor '%s' and batch size %s",
            table_name,
            SCHEMA,
            cursor_column,
            batch_size,
        )
        cur.execute(sql, (cursor,))

        columns = [desc[0] for desc in cur.description]

        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            yield rows, columns
    except Exception as exc:
        raise RuntimeError(
            f"Failed to extract data for table '{table_name}' from schema '{SCHEMA}': {exc}"
        ) from exc
