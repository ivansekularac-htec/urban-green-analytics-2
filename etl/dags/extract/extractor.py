"""Incremental extract logic: ``app.<table>`` deltas -> MinIO staging as Parquet.

Pure library code (no DAG objects). The DAG factory in ``extract_app_tables.py``
wires ``run_extract`` into one TaskFlow DAG per table.

Design notes:

* **Composite ``(updated_at, id)`` cursor.** ``updated_at`` is stored as epoch
  *seconds*, so several rows can share the same value. A cursor on ``updated_at``
  alone would either re-emit or skip rows on that boundary second. We instead use
  keyset pagination on the ``(updated_at, id)`` tuple, persisted as a small JSON
  object in an Airflow Variable (``extract_cursor__<table>``), editable from the
  UI. A legacy single-integer cursor is migrated transparently.

* **Safety lag.** Rows written in the last couple of seconds may still be part of
  an in-flight transaction. We compute ``run_cutoff = now - SAFETY_LAG_SECONDS``
  and never read past it, so a half-committed batch isn't captured behind a cursor
  that would then skip the rest. Configurable via the ``EXTRACT_SAFETY_LAG_SECONDS``
  env var (default 30); no compose change required.

* **Idempotency.** The high-watermark is snapshotted up front; rows are written
  with a single atomic S3 PUT per object; the cursor advances only afterwards. A
  crash mid-write leaves no partial object and an unmoved cursor, so a re-run
  reproduces the same key (overwrite) — no duplicate rows.
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

SCHEMA = "app"
CURSOR_COLUMN = "updated_at"
PRIMARY_KEY = "id"

# Rows newer than (now - lag) may still be mid-write (a transaction can take a few
# seconds to commit), so we don't read past the cutoff and risk skipping them.
SAFETY_LAG_SECONDS = int(os.environ.get("EXTRACT_SAFETY_LAG_SECONDS", "30"))

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
    raw = Variable.get(
        _cursor_key(table), default=DEFAULT_CURSOR, deserialize_json=True
    )
    if isinstance(raw, dict):
        return {
            "updated_at": int(raw.get("updated_at", 0)),
            "id": int(raw.get("id", 0)),
        }
    # Legacy format: a bare epoch-seconds integer.
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


def _high_watermark(
    pg, table: str, low: dict[str, int], run_cutoff: int
) -> dict[str, int] | None:
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


def _read_window(pg, table: str, low: dict[str, int], high: dict[str, int]):
    """Fetch rows in the keyset window (low, high] as a DataFrame.

    Uses the raw psycopg2 cursor and builds the DataFrame by hand: pandas'

    """
    import pandas as pd

    select_sql = f"""
        SELECT *
        FROM {SCHEMA}.{table}
        WHERE ({CURSOR_COLUMN} > %s OR ({CURSOR_COLUMN} = %s AND {PRIMARY_KEY} > %s))
          AND ({CURSOR_COLUMN} < %s OR ({CURSOR_COLUMN} = %s AND {PRIMARY_KEY} <= %s))
        ORDER BY {CURSOR_COLUMN}, {PRIMARY_KEY}
    """
    params = (
        low["updated_at"],
        low["updated_at"],
        low["id"],
        high["updated_at"],
        high["updated_at"],
        high["id"],
    )
    conn = pg.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(select_sql, params)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=columns)


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


def run_extract(
    table: str,
    partition_by: str | None = None,
    partition_label: str | None = None,
) -> None:
    """Extract one table's changes since its cursor and land them as Parquet."""
    import io

    import pandas as pd
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

    df = _read_window(pg, table, low, high)
    if df.empty:
        raise AirflowSkipException(
            f"No rows read for {SCHEMA}.{table} in window {low}..{high}."
        )

    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)
    bucket = os.environ["MINIO_STAGING_BUCKET"]
    # Range tag encodes the full (updated_at, id) window so the key shows exactly
    # which slice of changes the file covers.
    range_tag = f"{low['updated_at']}_{low['id']}__{high['updated_at']}_{high['id']}"

    written_keys: list[str] = []

    def _write(chunk: pd.DataFrame, key: str) -> None:
        buf = io.BytesIO()
        chunk.to_parquet(buf, engine="pyarrow", index=False)
        # Single atomic PUT; replace=True makes a re-run overwrite the same key.
        s3.load_bytes(buf.getvalue(), key=key, bucket_name=bucket, replace=True)
        written_keys.append(key)

    if partition_by:
        days = pd.to_datetime(df[partition_by], unit="s", utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        for day, group in df.groupby(days):
            key = f"app/{table}/{partition_label}={day}/{table}__{range_tag}.parquet"
            _write(group, key)
    else:
        key = f"app/{table}/{table}__{range_tag}.parquet"
        _write(df, key)

    # Advance the cursor only after every write above has succeeded.
    set_cursor(table, high)

    logger.info(
        "extract %s.%s: %d row(s), cursor %s -> %s, %d object(s) written",
        SCHEMA,
        table,
        len(df),
        low,
        high,
        len(written_keys),
    )
