"""SCD2 loader for dim_user_farm_role.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/user_roles/ (+ users, roles, dim_farm)
Target: urbangreen_dw.dim_user_farm_role

farm_id / farm_key = 0 means system-wide role (Postgres NULL farm_id).
Run after load_dim_farm.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import read_sql, write_table
from common.jobs import run_job
from common.lake import read_postgres
from common.transforms import build_scd2, latest_by_key
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def _load(spark: SparkSession) -> None:
    """Build user-role-farm SCD2 versions and write them to dim_user_farm_role."""
    ur = read_postgres(spark, "user_roles")
    if ur is None:
        logger.info("no user_roles data in lake; skipping")
        return

    users_raw = read_postgres(spark, "users")
    roles_raw = read_postgres(spark, "roles")
    if users_raw is None or roles_raw is None:
        logger.info("missing users/roles in lake; skipping")
        return

    users = latest_by_key(users_raw, "id").select(
        F.col("id").alias("user_id"),
        F.col("full_name").alias("user_full_name"),
    )
    roles = latest_by_key(roles_raw, "id").select(
        F.col("id").alias("role_id"),
        F.col("name").alias("role_name"),
    )
    farms = read_sql(
        spark,
        "SELECT farm_id, farm_key, name AS farm_name "
        "FROM dim_farm FINAL WHERE is_current = 1",
    )

    out = (
        build_scd2(ur, "id")
        .join(F.broadcast(users), "user_id", "left")
        .join(F.broadcast(roles), "role_id", "left")
        .join(F.broadcast(farms), "farm_id", "left")
        .select(
            F.col("id").alias("user_role_id"),
            F.col("user_id"),
            F.col("role_id"),
            F.coalesce(F.col("farm_key"), F.lit(0)).alias("farm_key"),
            F.coalesce(F.col("farm_id"), F.lit(0)).alias("farm_id"),
            F.coalesce(F.col("user_full_name"), F.lit("")).alias("user_full_name"),
            F.coalesce(F.col("role_name"), F.lit("")).alias("role_name"),
            F.coalesce(F.col("farm_name"), F.lit("")).alias("farm_name"),
            F.col("valid_from"),
            F.col("valid_to"),
            F.col("is_current"),
            F.col("_version"),
        )
    )
    write_table(out, "dim_user_farm_role")
    logger.info("dim_user_farm_role: load complete")


if __name__ == "__main__":
    run_job("load_dim_user_farm_role", _load)
