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

    Flow:
        1. Read last processed cursor
        2. Query Postgres with safety cutoff
        3. Stream results in chunks
        4. Write each chunk to MinIO
        5. Advance cursor after successful write
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

    cur.execute(query, (last_ts, last_ts, last_id, cutoff))

    columns = [c[0] for c in cur.description]

    # ---------------------------------------------------------
    # 3. READ FIRST CHUNK (IMPORTANT: determines SKIP safely)
    # ---------------------------------------------------------
    rows = cur.fetchmany(INGESTION_CHUNK_SIZE)

    if not rows:
        cur.close()
        conn.close()
        raise AirflowSkipException(f"No new rows found for table '{table}'")

    # ---------------------------------------------------------
    # 4. PROCESS CHUNKS
    # ---------------------------------------------------------
    rows_count = 0
    last_row = None

    while rows:
        df = pd.DataFrame(rows, columns=columns)

        # Ensure deterministic ordering
        df = df.sort_values([cursor_column, "id"])

        batch_first = df.iloc[0]
        batch_last = df.iloc[-1]

        start_cursor = {
            "updated_at": int(batch_first[cursor_column]),
            "id": int(batch_first["id"]),
        }

        end_cursor = {
            "updated_at": int(batch_last[cursor_column]),
            "id": int(batch_last["id"]),
        }

        # Write batch BEFORE moving cursor
        write_dataframe(
            df=df,
            config=config,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
        )

        rows_count += len(df)
        last_row = batch_last

        # next batch
        rows = cur.fetchmany(INGESTION_CHUNK_SIZE)

    # ---------------------------------------------------------
    # 5. CLEANUP DB RESOURCES
    # ---------------------------------------------------------
    cur.close()
    conn.close()

    # ---------------------------------------------------------
    # 6. UPDATE CURSOR (ONLY AFTER SUCCESS)
    # ---------------------------------------------------------
    cursor_after = {
        "updated_at": int(last_row[cursor_column]),
        "id": int(last_row["id"]),
    }

    set_cursor(table, cursor_column, last_row)

    print(f"[{table}] Cursor updated → {cursor_after}")

    # ---------------------------------------------------------
    # 7. RESULT
    # ---------------------------------------------------------
    return build_result(
        table=table,
        rows=rows_count,
        status="SUCCESS",
        cursor_before=cursor_before,
        cursor_after=cursor_after,
    )


def build_result(table, rows, status, cursor_before, cursor_after):
    """
    Standardized ingestion result object.
    """
    return {
        "table": table,
        "rows": rows,
        "status": status,
        "cursor_before": cursor_before,
        "cursor_after": cursor_after,
    }
