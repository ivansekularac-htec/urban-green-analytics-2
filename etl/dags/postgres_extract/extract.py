"""Incremental extract of app.* Postgres tables into MinIO staging as Parquet."""

import logging
import os
from datetime import datetime, timezone

import pandas as pd
from airflow.exceptions import AirflowSkipException
from airflow.providers.postgres.hooks.postgres import PostgresHook

from postgres_extract.cursor import (
    clear_pending,
    get_cursor,
    read_frozen_high,
    set_cursor,
    set_pending,
)
from postgres_extract.write import (
    flat_key,
    get_s3,
    partition_key,
    write_parquet,
)

logger = logging.getLogger(__name__)

POSTGRES_CONN_ID = "urbangreen_db"
SCHEMA = "app"
CURSOR_COLUMN = "updated_at"
PRIMARY_KEY = "id"
CHUNK_SIZE = int(os.environ.get("EXTRACT_CHUNK_SIZE", "200000"))


def format_cursor(value):
    """Turn an epoch-seconds cursor into a compact UTC stamp used in object keys."""
    return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def high_watermark(pg, table, cursor_from):
    """Return the largest cursor value above cursor_from, or None when nothing is new."""
    row = pg.get_first(
        f"SELECT MAX({CURSOR_COLUMN}) FROM {SCHEMA}.{table} WHERE {CURSOR_COLUMN} > %s",
        parameters=(cursor_from,),
    )
    return row[0] if row else None


def window_sql(table, cursor_from, cursor_to):
    """Build the SELECT and params for rows in the (cursor_from, cursor_to] window."""
    sql = f"""
        SELECT *
        FROM {SCHEMA}.{table}
        WHERE {CURSOR_COLUMN} > %s AND {CURSOR_COLUMN} <= %s
    """
    params = (cursor_from, cursor_to)
    return sql, params


def extract_single_file(pg, s3, table, cursor_from, cursor_to, run_window):
    """Read the whole window for a small table and write it as one Parquet object."""
    sql, params = window_sql(table, cursor_from, cursor_to)
    conn = pg.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    finally:
        conn.close()

    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        return 0, []

    key = flat_key(table, run_window)
    write_parquet(s3, df, key)
    return len(df), [key]


def split_by_day(df, partition_by):
    """Split a chunk into {day: rows} using the date of the partition column."""
    days = pd.to_datetime(df[partition_by], unit="s", utc=True).dt.strftime("%Y-%m-%d")
    buckets = {}
    for day in days.unique():
        buckets[day] = df[days == day]
    return buckets


def extract_partitioned(
    pg, s3, table, partition_by, partition_label, cursor_from, cursor_to, run_window
):
    """Stream a large table in chunks and write one Parquet per day per chunk."""
    sql, params = window_sql(table, cursor_from, cursor_to)
    conn = pg.get_conn()
    total_rows = 0
    keys = []
    try:
        with conn.cursor(name=f"extract_{table}") as cur:
            cur.itersize = CHUNK_SIZE
            cur.execute(sql, params)
            columns = None
            chunk_index = 0
            while True:
                rows = cur.fetchmany(CHUNK_SIZE)
                if not rows:
                    break
                if columns is None:
                    columns = [desc[0] for desc in cur.description]
                chunk_index += 1
                df = pd.DataFrame(rows, columns=columns)
                total_rows += len(df)
                for day, group in split_by_day(df, partition_by).items():
                    key = partition_key(
                        table, run_window, partition_label, day, chunk_index
                    )
                    write_parquet(s3, group, key)
                    keys.append(key)
    finally:
        conn.close()
    return total_rows, keys


def run_extract(table, partition_by=None, partition_label=None):
    """Extract new rows for one table, write them, then advance the cursor on success."""
    pg = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    cursor_from = get_cursor(table)

    cursor_to = read_frozen_high(table, cursor_from)
    if cursor_to is None:
        cursor_to = high_watermark(pg, table, cursor_from)
        if cursor_to is None or cursor_to <= cursor_from:
            raise AirflowSkipException(
                f"No new rows in {SCHEMA}.{table} since cursor {cursor_from}."
            )
        set_pending(table, cursor_to)

    s3 = get_s3()
    run_window = f"{format_cursor(cursor_from)}__{format_cursor(cursor_to)}"

    if partition_by:
        rows_written, keys = extract_partitioned(
            pg,
            s3,
            table,
            partition_by,
            partition_label,
            cursor_from,
            cursor_to,
            run_window,
        )
    else:
        rows_written, keys = extract_single_file(
            pg, s3, table, cursor_from, cursor_to, run_window
        )

    set_cursor(table, cursor_to)
    clear_pending(table)

    logger.info(
        f"extract {SCHEMA}.{table}: {rows_written} row(s), "
        f"cursor {cursor_from} -> {cursor_to}, {len(keys)} object(s) written"
    )
