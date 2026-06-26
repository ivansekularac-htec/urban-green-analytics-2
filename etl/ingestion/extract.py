import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook

from ingestion.state import get_cursor, set_cursor
from ingestion.storage import upload_parquet


def extract_table(config):
    """
    Executes incremental extraction of a single table from Postgres
    and writes the result into object storage (MinIO) as a Parquet file.

    This function is the core ingestion engine of the system.

    Pipeline steps:
    1. Reads incremental cursor from Airflow state (Variable)
    2. Queries Postgres for new/updated rows since last cursor
    3. Converts results into a Pandas DataFrame
    4. Writes DataFrame to a local Parquet file
    5. Uploads Parquet file to MinIO (S3-compatible storage)
    6. Advances the cursor ONLY after successful write
    7. Returns structured execution metadata

    Args:
        config (dict):
            Table ingestion configuration containing:
                - table (str): table name in Postgres
                - schema (str): database schema name
                - cursor_column (str): column used for incremental extraction
                - bucket (str): target MinIO bucket name

    Returns:
        dict:
            Structured execution result containing:
                - table (str): table name
                - rows (int): number of rows extracted
                - status (str): SUCCESS | SKIPPED | FAILED
                - cursor_before (dict): cursor state before extraction
                - cursor_after (dict): cursor state after successful extraction

    Notes:
        - Uses a composite cursor (updated_at + id) for deterministic ordering
        - Ensures idempotency by only advancing cursor after successful upload
        - Designed to be safely retryable in Airflow
    """

    table = config["table"]
    schema = config["schema"]
    cursor_column = config["cursor_column"]
    bucket = config["bucket"]

    # -----------------------
    # 1. CURSOR STATE
    # -----------------------
    last_ts, last_id = get_cursor(table)

    cursor_before = {
        "updated_at": last_ts,
        "id": last_id,
    }

    # -----------------------
    # 2. POSTGRES QUERY
    # -----------------------
    pg = PostgresHook(postgres_conn_id="urbangreen_db")
    conn = pg.get_conn()
    cur = conn.cursor()

    query = f"""
        SELECT *
        FROM {schema}.{table}
        WHERE
            {cursor_column} > %s
            OR ({cursor_column} = %s AND id > %s)
        ORDER BY {cursor_column}, id
    """

    cur.execute(query, (last_ts, last_ts, last_id))

    rows = cur.fetchall()
    columns = [c[0] for c in cur.description]

    cur.close()
    conn.close()

    # -----------------------
    # 3. NO DATA CASE
    # -----------------------
    if not rows:
        return build_result(
            table=table,
            rows_count=0,
            status="SKIPPED",
            cursor_before=cursor_before,
            cursor_after=cursor_before,
        )

    rows_count = len(rows)

    # -----------------------
    # 4. DATAFRAME
    # -----------------------
    df = pd.DataFrame(rows, columns=columns)

    parquet_path = f"/tmp/{table}.parquet"
    df.to_parquet(parquet_path, index=False)

    # -----------------------
    # 5. STORAGE (MINIO)
    # -----------------------
    object_key = f"{table}/{table}.parquet"
    upload_parquet(parquet_path, bucket, object_key)

    # -----------------------
    # 6. CURSOR UPDATE (ONLY AFTER SUCCESS)
    # -----------------------
    last_row = df.iloc[-1]

    cursor_after = {
        "updated_at": int(last_row[cursor_column]),
        "id": int(last_row["id"]),
    }

    set_cursor(table, cursor_column, last_row)

    print(f"[{table}] Cursor updated → {cursor_after}")

    # -----------------------
    # 7. RESULT
    # -----------------------
    return build_result(
        table=table,
        rows_count=rows_count,
        status="SUCCESS",
        cursor_before=cursor_before,
        cursor_after=cursor_after,
    )


def build_result(table, rows_count, status, cursor_before, cursor_after):
    """
    Builds a standardized execution result object for ingestion tracking.

    Args:
        table (str): table name
        rows_count (int): number of extracted rows
        status (str): execution status (SUCCESS, SKIPPED, FAILED)
        cursor_before (dict): cursor state before execution
        cursor_after (dict): cursor state after execution

    Returns:
        dict: standardized ingestion result payload
    """
    return {
        "table": table,
        "rows": rows_count,
        "status": status,
        "cursor_before": cursor_before,
        "cursor_after": cursor_after,
    }
