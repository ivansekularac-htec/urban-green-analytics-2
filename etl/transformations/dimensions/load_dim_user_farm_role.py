"""Load dim_user_farm_role from the raw Postgres user_roles extract.

Type 2 dimension over the user-role-farm assignment. Who managed which farm
in a given period is answered from here rather than from an attribute on
dim_farm or dim_user, because the relationship itself is what changes.

farm_id 0 stands for a system-wide role, which the source stores as NULL - an
administrator is not tied to any farm. farm_key carries the natural farm id
for the same reason as in dim_sensor: an assignment spans an interval and
cannot point at a single farm version.

Names of the user, role and farm are denormalized so the assignment reads on
its own without three extra joins. They are not tracked attributes: renaming a
farm does not end an assignment, so it must not open a new version here.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse, scd2
from common.spark import build_spark, read_raw_postgres
from common.transform import epoch_to_ts, latest_per_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "user_roles"
TARGET_TABLE = "dim_user_farm_role"
NATURAL_KEY = "user_role_id"
SURROGATE = "user_role_key"

# The assignment changes when it points somewhere else, not when one of the
# denormalized names is edited.
TRACKED_COLUMNS = ["user_id", "role_id", "farm_id", "farm_key"]

SYSTEM_WIDE_FARM = 0


def current_names(spark, query, key_column, name_column):
    """Read a current-state name lookup from the warehouse."""
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
            F.coalesce(F.col("farm_id"), F.lit(SYSTEM_WIDE_FARM)).cast("long").alias("farm_id"),
            epoch_to_ts("updated_at").alias("valid_from"),
        ).withColumn("farm_key", F.col("farm_id"))

        users = current_names(
            spark, "SELECT user_id, full_name FROM dim_user FINAL", "user_id", "full_name"
        ).withColumnRenamed("full_name", "user_full_name")

        roles = current_names(
            spark, "SELECT role_id, name FROM dim_role FINAL", "role_id", "name"
        ).withColumnRenamed("name", "role_name")

        farms = current_names(
            spark,
            "SELECT farm_id, name FROM dim_farm FINAL WHERE is_current = 1",
            "farm_id",
            "name",
        ).withColumnRenamed("name", "farm_name")

        incoming = (
            assignments.join(users, on="user_id", how="left")
            .join(roles, on="role_id", how="left")
            .join(farms, on="farm_id", how="left")
            .select(
                NATURAL_KEY,
                "user_id",
                "role_id",
                "farm_key",
                "farm_id",
                F.coalesce(F.col("user_full_name"), F.lit("")).alias("user_full_name"),
                F.coalesce(F.col("role_name"), F.lit("")).alias("role_name"),
                F.coalesce(F.col("farm_name"), F.lit("")).alias("farm_name"),
                "valid_from",
            )
        )

        scd2.apply_scd2(incoming, TARGET_TABLE, NATURAL_KEY, TRACKED_COLUMNS, SURROGATE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
