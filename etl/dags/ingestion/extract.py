import os

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook

from ingestion.write import write_parquet

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "urbangreen_db")
INGESTION_CHUNK_SIZE = int(os.getenv("INGESTION_CHUNK_SIZE", 100000))


def extract_and_write(config: dict) -> None:
    """
    Extracts incremental data from a Postgres table and writes it to MinIO as Parquet.

    This function:
    - Reads the last successful cursor value from Airflow Variables
    - Queries Postgres incrementally using that cursor
    - Streams results in chunks (to avoid high memory usage)
    - Writes each chunk to MinIO via the writer layer
    - Updates the cursor only after successful write completion

    Args:
        config (dict): Table configuration containing:
            - table (str): table name
            - schema (str): database schema
            - cursor_column (str): column used for incremental extraction
            - partition_column (str, optional): column used for partitioning output files
    """

    table = config["table"]
    schema = config["schema"]
    cursor_column = config["cursor_column"]

    # ---------------------------------------------------------
    # 1. Load last successful extraction cursor
    # ---------------------------------------------------------
    cursor_value = get_cursor(table)

    # ---------------------------------------------------------
    # 2. Build incremental SQL query
    # ---------------------------------------------------------
    pg = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = pg.get_conn()
    cur = conn.cursor()

    try:
        query = f"SELECT * FROM {schema}.{table}"
        params = []

        if cursor_value is not None:
            query += f" WHERE {cursor_column} > %s"
            params.append(cursor_value)

        cur.execute(query, params)

        # ---------------------------------------------------------
        # 3. Fetch first chunk
        # ---------------------------------------------------------
        rows = cur.fetchmany(INGESTION_CHUNK_SIZE)

        if not rows:
            raise AirflowSkipException(f"No new rows found for table '{table}'")

        max_cursor = cursor_value
        columns = [c[0] for c in cur.description]

        # ---------------------------------------------------------
        # 4. Stream data in chunks
        # ---------------------------------------------------------
        while rows:
            df = pd.DataFrame(rows, columns=columns)

            write_parquet(
                df=df,
                table=table,
                cursor_column=cursor_column,
                partition_column=config.get("partition_column"),
            )

            max_cursor = df[cursor_column].max()
            rows = cur.fetchmany(INGESTION_CHUNK_SIZE)

    finally:
        cur.close()
        conn.close()

    # ---------------------------------------------------------
    # 5. Persist cursor (ONLY after successful full run)
    # ---------------------------------------------------------
    set_cursor(table, max_cursor)


def get_cursor(table: str):
    """
    Retrieves the last successful extraction cursor for a given table.

    Returns:
        The stored cursor value (string or None if not set yet).
    """
    return Variable.get(
        f"extract_cursor_{table}",
        default_var=None,
    )


def set_cursor(table: str, value) -> None:
    """
    Persists the latest extraction cursor for a table.

    Args:
        table (str): table name
        value: cursor value (timestamp, integer, etc.)
    """
    Variable.set(
        f"extract_cursor_{table}",
        str(value),
    )
