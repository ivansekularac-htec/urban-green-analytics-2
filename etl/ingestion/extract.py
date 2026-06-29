from datetime import datetime, timedelta, timezone

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.providers.postgres.hooks.postgres import PostgresHook

from ingestion.config import (
    CURSOR_SAFETY_WINDOW_SECONDS,
    INGESTION_CHUNK_SIZE,
    POSTGRES_CONN_ID,
)
from ingestion.state import get_cursor, set_cursor
from ingestion.writer import write_dataframe


def extract_table(config):
    """
    Incrementally extracts data from a Postgres table and writes it to MinIO as Parquet.

    This is the core ingestion unit of the pipeline.

    Flow:
        1. Read last processed cursor from Airflow Variables
        2. Query Postgres for new rows using composite cursor (updated_at + id)
        3. Convert results to DataFrame
        4. Write Parquet file(s) to MinIO
        5. Update cursor ONLY after successful write
        6. Return execution metadata

    Cursor strategy:
        - Primary: updated_at (or configured cursor_column)
        - Secondary: id (for deterministic ordering)

    Args:
        config (dict): Table ingestion configuration

    Returns:
        dict: Execution result metadata
    """

    table = config["table"]
    schema = config["schema"]
    cursor_column = config["cursor_column"]

    # ---------------------------------------------------------
    # 1. LOAD CURSOR STATE
    # ---------------------------------------------------------
    last_ts, last_id = get_cursor(table)

    cursor_before = {
        "updated_at": last_ts,
        "id": last_id,
    }

    # ---------------------------------------------------------
    # 2. QUERY POSTGRES
    # ---------------------------------------------------------
    pg = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    conn = pg.get_conn()
    cur = conn.cursor()

    cutoff = int(
        (
            datetime.now(timezone.utc) - timedelta(seconds=CURSOR_SAFETY_WINDOW_SECONDS)
        ).timestamp()
    )

    query = f"""
        SELECT *
        FROM {schema}.{table}
        WHERE (
                {cursor_column} > %s
                OR ({cursor_column} = %s AND id > %s)
            )
        AND {cursor_column} <= %s
        ORDER BY {cursor_column}, id
    """

    cur.execute(
        query,
        (
            last_ts,
            last_ts,
            last_id,
            cutoff,
        ),
    )

    columns = [c[0] for c in cur.description]

    # ---------------------------------------------------------
    # 3. PROCESS RESULT SET IN CHUNKS
    # ---------------------------------------------------------

    rows_count = 0
    last_row = None
    first_batch = True

    while True:
        rows = cur.fetchmany(INGESTION_CHUNK_SIZE)

        if not rows:
            break

        if first_batch:
            first_batch = False

        df = pd.DataFrame(rows, columns=columns)

        # Preserve deterministic ordering
        df = df.sort_values([cursor_column, "id"])

        batch_first = df.iloc[0]
        batch_last = df.iloc[-1]

        write_dataframe(
            df=df,
            config=config,
            cursor_start=int(batch_first[cursor_column]),
            cursor_end=int(batch_last[cursor_column]),
        )

        rows_count += len(df)
        last_row = batch_last

    cur.close()
    conn.close()

    # ---------------------------------------------------------
    # 4. NO NEW DATA CASE
    # ---------------------------------------------------------

    if last_row is None:
        raise AirflowSkipException(f"No new rows found for table '{table}'")

    # ---------------------------------------------------------
    # 5. UPDATE CURSOR
    # ---------------------------------------------------------

    cursor_after = {
        "updated_at": int(last_row[cursor_column]),
        "id": int(last_row["id"]),
    }

    set_cursor(table, cursor_column, last_row)

    print(f"[{table}] Cursor updated → {cursor_after}")

    # ---------------------------------------------------------
    # 6. RETURN RESULT
    # ---------------------------------------------------------
    return build_result(
        table=table,
        rows_count=rows_count,
        status="SUCCESS",
        cursor_before=cursor_before,
        cursor_after=cursor_after,
    )


def build_result(table, rows_count, status, cursor_before, cursor_after):
    """
    Standardized ingestion result object.

    Used for logging, debugging, and future observability extensions.
    """
    return {
        "table": table,
        "rows": rows_count,
        "status": status,
        "cursor_before": cursor_before,
        "cursor_after": cursor_after,
    }
