"""Incremental extract logic: ``app.<table>`` deltas -> MinIO staging as Parquet.

Pure library code (no DAG objects). The DAG factory in ``extract_app_tables.py``
wires ``run_extract`` into one TaskFlow DAG per table.

Design notes:

* **Composite ``(updated_at, id)`` cursor.** ``updated_at`` is epoch *seconds*, so
  several rows can share a value; a cursor on ``updated_at`` alone would skip/re-emit
  rows on the boundary second. We keyset-paginate on the ``(updated_at, id)`` tuple,
  persisted as JSON in an Airflow Variable (``extract_cursor__<table>``), editable
  from the UI. A legacy single-integer cursor is migrated transparently.

* **Safety lag.** ``run_cutoff = now - SAFETY_LAG_SECONDS`` (default 30). Rows newer
  than the cutoff may still be mid-write, so we never read past it.

* **Memory.** The big fact table (``harvests``) is read with a **server-side cursor**
  in ``CHUNK_SIZE`` batches and written as Parquet part-files per chunk, so a full
  backfill of millions of rows never loads everything into memory at once. The small
  reference tables are read in one shot (they're lookup tables).

* **Idempotency.** The high-watermark is snapshotted up front; objects are written
  with single atomic S3 PUTs; the cursor advances only afterwards. Deterministic
  ordering (and part numbering) means a re-run reproduces the same keys (overwrite) —
  no duplicate rows, and the object count per partition doesn't grow.
"""

from __future__ import annotations

import logging
import os
import re

from airflow.exceptions import AirflowSkipException
from airflow.sdk import Variable

logger = logging.getLogger(__name__)

POSTGRES_CONN_ID = "urbangreen_db"
MINIO_CONN_ID = "urbangreen_minio"
# Default matches .env.example so a missing env var degrades gracefully.
MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")

SCHEMA = "app"
CURSOR_COLUMN = "updated_at"
PRIMARY_KEY = "id"

# Rows newer than (now - lag) may still be mid-write (a transaction can take a few
# seconds to commit), so we don't read past the cutoff and risk skipping them.
SAFETY_LAG_SECONDS = int(os.environ.get("EXTRACT_SAFETY_LAG_SECONDS", "30"))

# Batch size for the server-side cursor used on partitioned (large) tables.
CHUNK_SIZE = int(os.environ.get("EXTRACT_CHUNK_SIZE", "50000"))

DEFAULT_CURSOR = {"updated_at": 0, "id": 0}

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def _safe_identifier(name: str) -> str:
    """Guard table/column names before interpolating them into SQL."""
    if not _IDENTIFIER.fullmatch(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return name


def _cursor_key(table: str) -> str:
    return f"extract_cursor__{table}"


def get_cursor(table: str) -> dict[str, int]:
    """Read the per-table ``(updated_at, id)`` cursor; default to zero on first run.

    Tolerates a legacy single-integer cursor by treating it as ``id=0``.
    """
    raw = Variable.get(_cursor_key(table), default=DEFAULT_CURSOR, deserialize_json=True)
    if isinstance(raw, dict):
        return {"updated_at": int(raw.get("updated_at", 0)), "id": int(raw.get("id", 0))}
    return {"updated_at": int(raw), "id": 0}


def set_cursor(table: str, cursor: dict[str, int]) -> None:
    Variable.set(_cursor_key(table), cursor, serialize_json=True)


def _run_cutoff(pg) -> int:
    """Newest ``updated_at`` we're willing to read this run (now minus safety lag)."""
    value = pg.get_first(
        "SELECT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT - %s",
        parameters=(SAFETY_LAG_SECONDS,),
    )[0]
    return max(int(value), 0)


def _assert_table_shape(pg, table: str, partition_by: str | None) -> None:
    """Fail early with a clear error if the table lacks the columns we rely on."""
    required = {PRIMARY_KEY, CURSOR_COLUMN}
    if partition_by:
        required.add(partition_by)
    rows = pg.get_records(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        """,
        parameters=(SCHEMA, table),
    )
    present = {row[0] for row in rows}
    missing = sorted(required - present)
    if missing:
        raise ValueError(f"{SCHEMA}.{table} is missing required columns: {missing}")


def _high_watermark(pg, table: str, low: dict[str, int], run_cutoff: int) -> dict[str, int] | None:
    """Snapshot the newest ``(updated_at, id)`` in the (low, run_cutoff] window."""
    row = pg.get_first(
        f"""
        SELECT {CURSOR_COLUMN}, {PRIMARY_KEY}
        FROM {SCHEMA}.{table}
        WHERE ({CURSOR_COLUMN} > %s OR ({CURSOR_COLUMN} = %s AND {PRIMARY_KEY} > %s))
          AND {CURSOR_COLUMN} <= %s
        ORDER BY {CURSOR_COLUMN} DESC, {PRIMARY_KEY} DESC
        LIMIT 1
        """,
        parameters=(low["updated_at"], low["updated_at"], low["id"], run_cutoff),
    )
    if row is None:
        return None
    return {"updated_at": int(row[0]), "id": int(row[1])}


def _window_sql(table: str, low: dict[str, int], high: dict[str, int]):
    """Keyset window (low, high], ordered by the cursor tuple. Shared by both readers."""
    sql = f"""
        SELECT *
        FROM {SCHEMA}.{table}
        WHERE ({CURSOR_COLUMN} > %s OR ({CURSOR_COLUMN} = %s AND {PRIMARY_KEY} > %s))
          AND ({CURSOR_COLUMN} < %s OR ({CURSOR_COLUMN} = %s AND {PRIMARY_KEY} <= %s))
        ORDER BY {CURSOR_COLUMN}, {PRIMARY_KEY}
    """
    params = (
        low["updated_at"], low["updated_at"], low["id"],
        high["updated_at"], high["updated_at"], high["id"],
    )
    return sql, params


def _write_parquet(s3, dataframe, key: str) -> None:
    """Serialize a DataFrame to Parquet and upload it with a single atomic PUT."""
    import io

    buf = io.BytesIO()
    dataframe.to_parquet(buf, engine="pyarrow", index=False)
    s3.load_bytes(buf.getvalue(), key=key, bucket_name=MINIO_STAGING_BUCKET, replace=True)
    logger.info("wrote %d row(s) -> s3://%s/%s", len(dataframe), MINIO_STAGING_BUCKET, key)


def _extract_single_file(pg, s3, table: str, low, high, range_tag: str):
    """Small reference tables: read the window in one shot, write one object."""
    import pandas as pd

    sql, params = _window_sql(table, low, high)
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

    key = f"app/{table}/{table}__{range_tag}.parquet"
    _write_parquet(s3, df, key)
    return len(df), [key]


def _extract_partitioned_stream(pg, s3, table, partition_by, partition_label, low, high, range_tag):
    """Large partitioned table (harvests): stream via a server-side cursor in
    ``CHUNK_SIZE`` batches, writing Parquet part-files per chunk and per day. Memory
    stays bounded to one chunk regardless of how big the backfill is.
    """
    import pandas as pd

    sql, params = _window_sql(table, low, high)
    conn = pg.get_conn()
    total_rows = 0
    keys: list[str] = []
    try:
        # Named cursor => server-side: fetchmany streams batches instead of loading all.
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
                days = pd.to_datetime(df[partition_by], unit="s", utc=True).dt.strftime("%Y-%m-%d")
                for day, group in df.groupby(days):
                    key = (
                        f"app/{table}/{partition_label}={day}/"
                        f"{table}__{range_tag}__part{chunk_index:04d}.parquet"
                    )
                    _write_parquet(s3, group, key)
                    keys.append(key)
    finally:
        conn.close()
    return total_rows, keys


def run_extract(
    table: str,
    partition_by: str | None = None,
    partition_label: str | None = None,
) -> None:
    """Extract one table's changes since its cursor and land them as Parquet."""
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    table = _safe_identifier(table)
    if partition_by is not None:
        partition_by = _safe_identifier(partition_by)

    low = get_cursor(table)

    pg = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    _assert_table_shape(pg, table, partition_by)
    run_cutoff = _run_cutoff(pg)

    high = _high_watermark(pg, table, low, run_cutoff)
    if high is None:
        raise AirflowSkipException(
            f"No new rows in {SCHEMA}.{table} since cursor {low} (run_cutoff={run_cutoff})."
        )

    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)
    # Range tag encodes the full (updated_at, id) window so the key shows exactly
    # which slice of changes the file covers.
    range_tag = f"{low['updated_at']}_{low['id']}__{high['updated_at']}_{high['id']}"

    if partition_by:
        rows_written, keys = _extract_partitioned_stream(
            pg, s3, table, partition_by, partition_label, low, high, range_tag
        )
    else:
        rows_written, keys = _extract_single_file(pg, s3, table, low, high, range_tag)

    if rows_written == 0:
        raise AirflowSkipException(f"No rows read for {SCHEMA}.{table} in window {low}..{high}.")

    # Advance the cursor only after every write above has succeeded.
    set_cursor(table, high)

    logger.info(
        "extract %s.%s: %d row(s), cursor %s -> %s, %d object(s) written",
        SCHEMA,
        table,
        rows_written,
        low,
        high,
        len(keys),
    )
