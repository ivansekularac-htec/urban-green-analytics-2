"""Load fact_daily_farm_metrics from fact_harvests and fact_sensor_readings.

One row per farm per day, combining the harvest side (yield, quality split) and
the sensor side (reading counts, anomalies, energy). It is the row the farm
leaderboard is built from, so the two atomic facts are rolled up to a common
farm/day grain here once rather than in every downstream query.

energy_kwh is the summed value of the energy sensor type only, isolated from the
other reading counts. premium_yield_kg splits the harvest by whether its grade
counts as premium.

Recomputed in full from the fact tables on every run; the ReplacingMergeTree
keyed on the daily grain absorbs late facts without tracking changed days.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse
from common.spark import build_spark

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TARGET_TABLE = "fact_daily_farm_metrics"
ENERGY_SENSOR_TYPE = "Energy Usage"

# Business grain of the daily rollup. farm_key is the SCD2 surrogate and is
# not part of it: it changes on every farm version, so keeping it in the grain
# would split one farm-day into several rows and let stale refreshes survive.
# Each side derives a single farm_key as a denormalized value instead.
GRAIN = ["farm_id", "metric_date", "date_key"]


def harvest_side(spark):
    """Daily yield and quality split per farm."""
    harvests = clickhouse.read_query(
        spark,
        "SELECT farm_id, farm_key, harvest_date, date_key, quality_grade_id, "
        "weight_kg FROM fact_harvests FINAL",
    )
    recent = harvests

    grades = clickhouse.read_query(
        spark, "SELECT quality_grade_id, is_premium FROM dim_quality_grade FINAL"
    )
    joined = recent.join(grades, on="quality_grade_id", how="left").withColumn(
        "is_premium", F.coalesce(F.col("is_premium"), F.lit(0))
    )

    premium = F.when(F.col("is_premium") == 1, F.col("weight_kg")).otherwise(0)
    non_premium = F.when(F.col("is_premium") == 0, F.col("weight_kg")).otherwise(0)

    return (
        joined.withColumnRenamed("harvest_date", "metric_date")
        .groupBy(*GRAIN)
        .agg(
            F.max("farm_key").alias("h_farm_key"),
            F.sum("weight_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.count(F.lit(1)).cast("int").alias("harvest_count"),
            F.sum(premium).cast("decimal(18,3)").alias("premium_yield_kg"),
            F.sum(non_premium).cast("decimal(18,3)").alias("non_premium_yield_kg"),
        )
    )


def sensor_side(spark):
    """Daily reading counts, anomalies and energy per farm."""
    readings = clickhouse.read_query(
        spark,
        "SELECT r.farm_id AS farm_id, r.farm_key AS farm_key, r.reading_date AS reading_date, "
        "r.date_key AS date_key, r.sensor_type_key AS sensor_type_key, r.value AS value, "
        "r.is_anomaly AS is_anomaly, r.reading_ts AS reading_ts FROM fact_sensor_readings r FINAL",
    )
    recent = readings.withColumnRenamed("reading_date", "metric_date")

    energy_types = clickhouse.read_query(
        spark,
        "SELECT sensor_type_id AS sensor_type_key FROM dim_sensor_type FINAL "
        f"WHERE name = '{ENERGY_SENSOR_TYPE}'",
    )
    energy_ids = [row["sensor_type_key"] for row in energy_types.collect()]
    is_energy = F.col("sensor_type_key").isin(energy_ids) if energy_ids else F.lit(False)
    energy_value = F.when(is_energy, F.col("value")).otherwise(0.0)

    return recent.groupBy(*GRAIN).agg(
        F.max("farm_key").alias("s_farm_key"),
        F.count(F.lit(1)).cast("long").alias("reading_count"),
        F.sum("is_anomaly").cast("long").alias("anomaly_count"),
        F.sum(F.lit(1) - F.col("is_anomaly")).cast("long").alias("in_range_count"),
        F.sum(energy_value).cast("double").alias("energy_kwh"),
        F.max("reading_ts").alias("last_sensor_reading_ts"),
    )


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        harvests = harvest_side(spark)
        sensors = sensor_side(spark)

        combined = harvests.join(sensors, on=GRAIN, how="fullouter")

        dates = clickhouse.read_query(
            spark, "SELECT date_key, year_week FROM dim_date"
        )
        combined = combined.join(dates, on="date_key", how="left")

        target = combined.select(
            "metric_date",
            "date_key",
            # A farm-day may come from either side of the full outer join, so the
            # surrogate is taken from whichever side has it.
            F.coalesce(F.col("h_farm_key"), F.col("s_farm_key"), F.lit(0)).alias("farm_key"),
            "farm_id",
            F.coalesce(F.col("year_week"), F.lit(0)).alias("year_week"),
            F.coalesce(F.col("total_yield_kg"), F.lit(0)).cast("decimal(18,3)").alias("total_yield_kg"),
            F.coalesce(F.col("harvest_count"), F.lit(0)).cast("int").alias("harvest_count"),
            F.coalesce(F.col("premium_yield_kg"), F.lit(0)).cast("decimal(18,3)").alias("premium_yield_kg"),
            F.coalesce(F.col("non_premium_yield_kg"), F.lit(0)).cast("decimal(18,3)").alias("non_premium_yield_kg"),
            F.coalesce(F.col("energy_kwh"), F.lit(0.0)).cast("double").alias("energy_kwh"),
            F.coalesce(F.col("reading_count"), F.lit(0)).cast("long").alias("reading_count"),
            F.coalesce(F.col("anomaly_count"), F.lit(0)).cast("long").alias("anomaly_count"),
            F.coalesce(F.col("in_range_count"), F.lit(0)).cast("long").alias("in_range_count"),
            F.col("last_sensor_reading_ts"),
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
