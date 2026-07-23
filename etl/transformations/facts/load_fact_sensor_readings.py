"""Load fact_sensor_readings from the raw Kafka sensor readings.

Incremental by event date: the streaming sink partitions the raw zone by
event_date, so the loader reads only the partitions at or after the cursor
instead of scanning a table that grows without bound. The cursor moves only
after the write succeeded, and the target is a ReplacingMergeTree, so a replay
of the last window collapses instead of duplicating.

The cursor keeps the last processed date rather than the last instant, because
readings for a day keep arriving while that day is open. Reprocessing the whole
boundary day is what makes late arrivals reach the warehouse.

is_anomaly is evaluated against the thresholds that applied when the reading
was taken, not against today's. Both the farm version and the sensor type
version are therefore resolved as of reading_ts.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse, facts, state
from common.spark import build_spark, read_raw_kafka

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

KAFKA_TOPIC = "sensor_readings"
TARGET_TABLE = "fact_sensor_readings"
JOB_NAME = "load_fact_sensor_readings"

UNKNOWN_FARM_KEY = 0

# Thresholds used when the sensor type version cannot be resolved. Chosen so
# no reading is flagged as an anomaly on missing reference data - a false
# anomaly is worse than a missed one, because it sends someone to inspect a
# healthy farm.
NO_ANOMALY_MIN = float("-inf")
NO_ANOMALY_MAX = float("inf")


def main():
    spark = build_spark(JOB_NAME)
    try:
        raw = read_raw_kafka(spark, KAFKA_TOPIC)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        cursor = state.read_cursor(spark, JOB_NAME) or {}
        last_date = cursor.get("event_date")

        if last_date:
            # Re-read the boundary day so readings that arrived after the last
            # run still land in the warehouse.
            window = raw.filter(F.col("event_date") >= F.lit(last_date))
        else:
            window = raw

        if window.isEmpty():
            logger.info(f"no readings at or after {last_date}")
            return

        readings = window.select(
            F.col("farm_sensor_id").cast("long").alias("sensor_key"),
            F.col("farm_id").cast("long").alias("farm_id"),
            F.col("sensor_type_id").cast("long").alias("sensor_type_key"),
            F.col("value").cast("double").alias("value"),
            F.col("timestamp").cast("long").cast("timestamp").alias("reading_ts"),
        )

        readings = (
            readings.withColumn("reading_date", F.to_date(F.col("reading_ts")))
            .withColumn("date_key", facts.date_key("reading_ts"))
            .withColumn("time_key", facts.time_key("reading_ts"))
            .withColumn(
                "reading_key", F.xxhash64(F.col("sensor_key"), F.col("reading_ts"))
            )
        )

        farm_versions = clickhouse.read_query(
            spark, "SELECT farm_id, farm_key, valid_from, valid_to FROM dim_farm FINAL"
        )

        with_farm = facts.as_of_version(
            readings,
            farm_versions,
            "farm_id",
            "reading_ts",
            [("farm_key", "farm_key", UNKNOWN_FARM_KEY)],
        )

        type_versions = clickhouse.read_query(
            spark,
            "SELECT sensor_type_id AS sensor_type_key, optimal_min, optimal_max, "
            "valid_from, valid_to FROM dim_sensor_type FINAL",
        )

        with_thresholds = facts.as_of_version(
            with_farm,
            type_versions,
            "sensor_type_key",
            "reading_ts",
            [
                ("optimal_min", "optimal_min", NO_ANOMALY_MIN),
                ("optimal_max", "optimal_max", NO_ANOMALY_MAX),
            ],
        )

        target = with_thresholds.withColumn(
            "is_anomaly",
            (
                (F.col("value") < F.col("optimal_min"))
                | (F.col("value") > F.col("optimal_max"))
            ).cast("tinyint"),
        ).select(
            "reading_key",
            "farm_key",
            "farm_id",
            "sensor_key",
            "sensor_type_key",
            "date_key",
            "time_key",
            "reading_ts",
            "reading_date",
            "value",
            "is_anomaly",
        )

        clickhouse.write_table(target, TARGET_TABLE)

        high_water = target.agg(F.max("reading_date")).collect()[0][0]
        state.write_cursor(spark, JOB_NAME, {"event_date": str(high_water)})
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
