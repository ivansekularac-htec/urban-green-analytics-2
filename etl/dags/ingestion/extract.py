import os

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook

from ingestion.write import write_parquet

# ---------------------------------------------------------
# Environment Variables
# ---------------------------------------------------------
POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "urbangreen_db")
INGESTION_CHUNK_SIZE = int(os.getenv("INGESTION_CHUNK_SIZE", 100000))


def extract_and_write(config):

    table = config["table"]
    schema = config["schema"]
    cursor_column = config["cursor_column"]

    # ---------------------------------------------------------
    # 1. LOAD CURSOR STATE
    # ---------------------------------------------------------

    cursor_value = get_cursor(table)

    # ---------------------------------------------------------
    # 2. QUERY POSTGRES
    # ---------------------------------------------------------

    pg = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = pg.get_conn()
    cur = conn.cursor()

    query = f"SELECT * FROM {schema}.{table}"

    params = []

    if cursor_value is not None:
        query += f" WHERE {cursor_column} > %s"
        params.append(cursor_value)

    query += f" ORDER BY {cursor_column}"

    cur.execute(query, params)

    # ---------------------------------------------------------
    # 3. READ FIRST CHUNK (IMPORTANT: determines SKIP safely)
    # ---------------------------------------------------------
    rows = cur.fetchmany(INGESTION_CHUNK_SIZE)

    if not rows:
        cur.close()
        conn.close()
        raise AirflowSkipException(f"No new rows found for table '{table}'")

    part = 1
    max_cursor = cursor_value

    columns = [c[0] for c in cur.description]

    while rows:
        df = pd.DataFrame(rows, columns=columns)

        start_cursor = df[cursor_column].min()
        end_cursor = df[cursor_column].max()

        object_key = f"updated_at={start_cursor}_{end_cursor}_{part}.parquet"

        write_parquet(
            df=df,
            table=table,
            object_key=object_key,
            partition_column=config.get("partition_column"),
        )

        max_cursor = end_cursor

        part += 1
        rows = cur.fetchmany(INGESTION_CHUNK_SIZE)

    # ---------------------------------------------------------
    # 4. CLEANUP DB RESOURCES
    # ---------------------------------------------------------
    cur.close()
    conn.close()

    # ---------------------------------------------------------
    # 6. UPDATE CURSOR (ONLY AFTER SUCCESS)
    # ---------------------------------------------------------
    set_cursor(table, max_cursor)


def get_cursor(table: str):
    return Variable.get(
        f"extract_cursor_{table}",
        default_var=None,
    )


def set_cursor(table: str, value) -> None:
    Variable.set(
        f"extract_cursor_{table}",
        str(value),
    )
