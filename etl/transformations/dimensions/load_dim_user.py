"""Type-1 loader for dim_user.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/users/
Target: urbangreen_dw.dim_user

password_hash is intentionally omitted.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import write_table
from common.jobs import run_job
from common.lake import read_postgres
from common.transforms import latest_by_key
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def _load(spark: SparkSession) -> None:
    """Load the latest user rows into dim_user."""
    raw = read_postgres(spark, "users")
    if raw is None:
        print("no users data in lake; skipping")
        return

    out = latest_by_key(raw, "id").select(
        F.col("id").alias("user_id"),
        F.col("email"),
        F.col("full_name"),
        F.col("is_active").cast("tinyint"),
        F.timestamp_seconds("created_at").alias("created_at"),
    )
    write_table(out, "dim_user")
    print(f"dim_user: wrote {out.count()} row(s)")


if __name__ == "__main__":
    run_job("load_dim_user", _load)
