"""Type-1 loader for dim_role.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/roles/
Target: urbangreen_dw.dim_role
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import write_table
from common.jobs import run_job
from common.lake import read_postgres
from common.transforms import latest_by_key
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def _load(spark: SparkSession) -> None:
    """Load the latest role rows from the lake into dim_role."""
    raw = read_postgres(spark, "roles")
    if raw is None:
        logger.info("no roles data in lake; skipping")
        return

    out = latest_by_key(raw, "id").select(
        F.col("id").alias("role_id"),
        F.col("name"),
        F.coalesce(F.col("description"), F.lit("")).alias("description"),
    )
    write_table(out, "dim_role")
    logger.info(f"dim_role: wrote {out.count()} row(s)")


if __name__ == "__main__":
    run_job("load_dim_role", _load)
