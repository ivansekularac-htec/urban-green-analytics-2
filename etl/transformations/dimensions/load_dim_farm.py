"""Load dim_farm from the raw Postgres farms extract.

Type 2 dimension. A farm changes name, size or status over time and reports
about a past period must show what was true then, so every change opens a new
version instead of overwriting the old one.

Infrastructure and growing system names are denormalized onto the farm, which
is what keeps the schema a star: dashboards group by them without joining two
extra lookup tables.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import scd2
from common.spark import build_spark, read_raw_postgres
from common.transform import epoch_to_ts, latest_per_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "farms"
INFRASTRUCTURE_TABLE = "farm_infrastructure_types"
GROWING_SYSTEM_TABLE = "growing_system_types"
TARGET_TABLE = "dim_farm"
NATURAL_KEY = "farm_id"
SURROGATE = "farm_key"

TRACKED_COLUMNS = [
    "name",
    "city",
    "size_m2",
    "growing_beds_count",
    "status",
    "infrastructure_type_id",
    "infrastructure_type_name",
    "growing_system_type_id",
    "growing_system_type_name",
]


def lookup_names(spark, table, id_alias, name_alias):
    """Read a reference table as an id/name pair, or None when not extracted."""
    raw = read_raw_postgres(spark, table)
    if raw is None:
        return None
    return latest_per_key(raw, "id").select(
        F.col("id").cast("long").alias(id_alias),
        F.col("name").cast("string").alias(name_alias),
    )


def attach(df, lookup, join_column, name_column):
    """Left join a reference name onto the farm.

    Left on purpose: a farm whose reference row has not reached the raw zone
    yet still belongs in the dimension, only without that name. An inner join
    would drop the farm, and every fact row pointing at it would join to
    nothing.
    """
    if lookup is None:
        logger.warning(f"no extract for {name_column}; leaving it empty")
        return df.withColumn(name_column, F.lit(""))
    joined = df.join(lookup, on=join_column, how="left")
    return joined.withColumn(name_column, F.coalesce(F.col(name_column), F.lit("")))


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        raw = read_raw_postgres(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        farms = latest_per_key(raw, "id").select(
            F.col("id").cast("long").alias(NATURAL_KEY),
            F.col("name").cast("string").alias("name"),
            F.coalesce(F.col("city"), F.lit("")).cast("string").alias("city"),
            F.coalesce(F.col("size_m2"), F.lit(0)).cast("decimal(10,3)").alias("size_m2"),
            F.coalesce(F.col("growing_beds_count"), F.lit(0)).cast("int").alias("growing_beds_count"),
            F.col("status").cast("string").alias("status"),
            F.col("infrastructure_type_id").cast("long").alias("infrastructure_type_id"),
            F.col("growing_system_type_id").cast("long").alias("growing_system_type_id"),
            epoch_to_ts("updated_at").alias("valid_from"),
        )

        farms = attach(
            farms,
            lookup_names(spark, INFRASTRUCTURE_TABLE, "infrastructure_type_id", "infrastructure_type_name"),
            "infrastructure_type_id",
            "infrastructure_type_name",
        )
        farms = attach(
            farms,
            lookup_names(spark, GROWING_SYSTEM_TABLE, "growing_system_type_id", "growing_system_type_name"),
            "growing_system_type_id",
            "growing_system_type_name",
        )

        incoming = farms.select(
            NATURAL_KEY,
            "name",
            "city",
            "size_m2",
            "growing_beds_count",
            "status",
            "infrastructure_type_id",
            "infrastructure_type_name",
            "growing_system_type_id",
            "growing_system_type_name",
            "valid_from",
        )

        scd2.apply_scd2(incoming, TARGET_TABLE, NATURAL_KEY, TRACKED_COLUMNS, SURROGATE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
