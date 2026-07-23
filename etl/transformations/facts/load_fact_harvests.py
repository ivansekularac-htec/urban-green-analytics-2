"""Load fact_harvests from the raw Postgres harvests extract.

Incremental: the loader reads the cursor, processes only rows changed above it,
and advances the cursor only after the write succeeded. A crash in between
leaves the old cursor in place, so the next run replays the same window; the
target is a ReplacingMergeTree keyed on the harvest identity, so the replay
collapses instead of double counting.

farm_key is resolved as of harvested_at rather than taken from the current farm
version, so a report over a past period keeps showing the farm as it was then.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse, facts, state
from common.spark import build_spark, read_raw_postgres_partitioned
from common.transform import epoch_to_ts, latest_per_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "harvests"
TARGET_TABLE = "fact_harvests"
JOB_NAME = "load_fact_harvests"

# Farms that never resolved keep this, so unmatched rows stay visible in the
# warehouse instead of being silently attributed to an existing farm.
UNKNOWN_FARM_KEY = 0


def main():
    spark = build_spark(JOB_NAME)
    try:
        raw = read_raw_postgres_partitioned(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        cursor = state.read_cursor(spark, JOB_NAME) or {}
        last_updated_at = cursor.get("updated_at", 0)

        changed = raw.filter(F.col("updated_at") > F.lit(last_updated_at))
        if changed.isEmpty():
            logger.info(f"no harvests above cursor {last_updated_at}")
            return

        current = latest_per_key(changed, "id")

        harvests = current.select(
            F.col("id").cast("long").alias("harvest_id"),
            F.col("farm_id").cast("long").alias("farm_id"),
            F.col("crop_id").cast("long").alias("crop_id"),
            F.col("quality_grade_id").cast("long").alias("quality_grade_id"),
            F.col("weight_kg").cast("decimal(10,3)").alias("weight_kg"),
            epoch_to_ts("created_at").alias("harvested_at"),
            F.col("updated_at").cast("long").alias("_source_updated_at"),
        )

        harvests = (
            harvests.withColumn("harvest_date", F.to_date(F.col("harvested_at")))
            .withColumn("date_key", facts.date_key("harvested_at"))
            .withColumn("time_key", facts.time_key("harvested_at"))
            .withColumn("harvest_key", F.xxhash64(F.col("harvest_id")))
        )

        farm_versions = clickhouse.read_query(
            spark, "SELECT farm_id, farm_key, valid_from, valid_to FROM dim_farm FINAL"
        )

        enriched = facts.as_of_version(
            harvests,
            farm_versions,
            "farm_id",
            "harvested_at",
            [("farm_key", "farm_key", UNKNOWN_FARM_KEY)],
        )

        target = enriched.select(
            "harvest_key",
            "harvest_id",
            "farm_key",
            "farm_id",
            "crop_id",
            "quality_grade_id",
            "date_key",
            "time_key",
            "harvested_at",
            "harvest_date",
            "weight_kg",
        )

        clickhouse.write_table(target, TARGET_TABLE)

        high_water = enriched.agg(F.max("_source_updated_at")).collect()[0][0]
        state.write_cursor(spark, JOB_NAME, {"updated_at": int(high_water)})
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
