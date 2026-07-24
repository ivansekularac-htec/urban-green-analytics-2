"""Per-loader cursor stored in the warehouse_load_state table.

A fact loader reads its cursor, processes only the slice above it, and writes
the new cursor back only after the data write succeeded. A crash between those
two steps leaves the old cursor in place, so the next run replays the same
window; the target tables are ReplacingMergeTree keyed on the event identity,
so the replay collapses instead of double-counting.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from common import clickhouse

logger = logging.getLogger(__name__)

STATE_TABLE = "warehouse_load_state"

STATE_SCHEMA = (
    "job_name string, cursor_json string, last_success_at timestamp, "
    "run_key string, _version long"
)


def read_cursor(spark, job_name):
    """Return the saved cursor for a loader, or None on the first ever run.

    FINAL is required because the state table is a ReplacingMergeTree and a
    previous write may not have merged yet.
    """
    query = (
        f"SELECT cursor_json FROM {STATE_TABLE} FINAL "
        f"WHERE job_name = '{job_name}'"
    )
    rows = clickhouse.read_query(spark, query).collect()
    if not rows:
        logger.info(f"no cursor for {job_name}; treating as first run")
        return None
    return json.loads(rows[0]["cursor_json"])


def write_cursor(spark, job_name, cursor):
    """Persist the cursor for a loader. Call only after all writes succeeded.

    _version is the load time in milliseconds so a later run always wins the
    ReplacingMergeTree merge for this job_name.
    """
    now = datetime.now(timezone.utc)
    row = [
        (
            job_name,
            json.dumps(cursor, sort_keys=True),
            now,
            str(uuid.uuid4()),
            int(now.timestamp() * 1000),
        )
    ]
    df = spark.createDataFrame(row, schema=STATE_SCHEMA)
    clickhouse.write_table(df, STATE_TABLE)
    logger.info(f"cursor for {job_name} advanced to {cursor}")
