"""Load dim_user_farm_role from the raw Postgres user_roles extract."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import clickhouse, scd2
from common.spark import build_spark, read_raw_postgres
from common.transform import epoch_to_ts, latest_per_key
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "user_roles"
TARGET_TABLE = "dim_user_farm_role"
NATURAL_KEY = "user_role_id"
SURROGATE = "user_role_key"

TRACKED_COLUMNS = ["user_id", "role_id", "farm_id", "farm_key"]

SYSTEM_WIDE_FARM = 0


def current_names(spark, query, key_column, name_column):
    return clickhouse.read_query(spark, query).select(
        F.col(key_column).cast("long").alias(key_column),
        F.col(name_column).cast("string").alias(name_column),
    )


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")

    try:
        raw = read_raw_postgres(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        assignments = latest_per_key(raw, "id").select(
            F.col("id").cast("long").alias(NATURAL_KEY),
            F.col("user_id").cast("long").alias("user_id"),
            F.col("role_id").cast("long").alias("role_id"),
            F.coalesce(F.col("farm_id"), F.lit(SYSTEM_WIDE_FARM))
            .cast("long")
            .alias("farm_id"),
            epoch_to_ts("updated_at").alias("valid_from"),
        )

        users = current_names(
            spark,
            "SELECT user_id, full_name FROM dim_user FINAL",
            "user_id",
            "full_name",
        ).withColumnRenamed("full_name", "user_full_name")

        roles = current_names(
            spark,
            "SELECT role_id, name FROM dim_role FINAL",
            "role_id",
            "name",
        ).withColumnRenamed("name", "role_name")

        farms = clickhouse.read_query(
            spark,
            """
                SELECT
                    farm_key,
                    farm_id,
                    name
                FROM dim_farm FINAL
                WHERE is_current = 1
                """,
        ).select(
            F.col("farm_key").alias("farm_key"),
            F.col("farm_id").cast("long").alias("farm_id"),
            F.col("name").cast("string").alias("farm_name"),
        )

        incoming = (
            assignments.join(users, "user_id", "left")
            .join(roles, "role_id", "left")
            .join(farms, "farm_id", "left")
            .select(
                NATURAL_KEY,
                "user_id",
                "role_id",
                F.coalesce(F.col("farm_key"), F.lit(0)).alias("farm_key"),
                "farm_id",
                F.coalesce(F.col("user_full_name"), F.lit("")).alias("user_full_name"),
                F.coalesce(F.col("role_name"), F.lit("")).alias("role_name"),
                F.coalesce(F.col("farm_name"), F.lit("")).alias("farm_name"),
                "valid_from",
            )
        )

        scd2.apply_scd2(
            incoming,
            TARGET_TABLE,
            NATURAL_KEY,
            TRACKED_COLUMNS,
            SURROGATE,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
