"""Refresh combined daily farm metrics from quality and sensor aggregates."""

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

ETL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETL_ROOT))

from transformations.common.clickhouse import read_clickhouse_table
from transformations.common.config import load_settings
from transformations.common.spark_session import build_spark_session
from transformations.common.staging import full_refresh_table

JOB_NAME = "refresh_daily_farm_metrics"
TARGET_TABLE = "fact_daily_farm_metrics"

GROUP_KEYS = [
    "metric_date",
    "date_key",
    "farm_key",
    "farm_id",
]


def aggregate_quality(
    metrics: DataFrame,
    grades: DataFrame,
) -> DataFrame:
    source = metrics.join(
        grades.select(
            "quality_grade_id",
            "is_premium",
        ),
        "quality_grade_id",
        "left",
    )

    return source.groupBy(*GROUP_KEYS).agg(
        F.sum("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
        F.sum("harvest_count").cast("int").alias("harvest_count"),
        F.sum(
            F.when(
                F.col("is_premium") == 1,
                F.col("total_yield_kg"),
            ).otherwise(0)
        )
        .cast("decimal(18,3)")
        .alias("premium_yield_kg"),
    )


def aggregate_sensors(
    metrics: DataFrame,
    sensor_types: DataFrame,
) -> DataFrame:
    source = metrics.join(
        sensor_types.select(
            "sensor_type_key",
            "unit",
        ),
        "sensor_type_key",
        "left",
    )

    is_energy = F.lower(F.trim(F.col("unit"))) == F.lit("kwh")

    return source.groupBy(*GROUP_KEYS).agg(
        F.sum(
            F.when(
                is_energy,
                F.col("sum_value"),
            ).otherwise(0.0)
        ).alias("energy_kwh"),
        F.sum("reading_count").alias("reading_count"),
        F.sum("anomaly_count").alias("anomaly_count"),
        F.sum("in_range_count").alias("in_range_count"),
    )


def aggregate_last_reading(
    readings: DataFrame,
) -> DataFrame:
    return readings.groupBy(
        F.col("reading_date").alias("metric_date"),
        "date_key",
        "farm_key",
        "farm_id",
    ).agg(F.max("reading_ts").alias("last_sensor_reading_ts"))


def combine_metrics(
    quality: DataFrame,
    sensors: DataFrame,
    last_reading: DataFrame,
    dates: DataFrame,
) -> DataFrame:
    combined = (
        quality.join(sensors, GROUP_KEYS, "full")
        .join(last_reading, GROUP_KEYS, "left")
        .join(
            dates.select("date_key", "year_week"),
            "date_key",
            "left",
        )
    )

    zero_yield = F.lit(0).cast("decimal(18,3)")

    total_yield = F.coalesce(
        F.col("total_yield_kg"),
        zero_yield,
    )

    premium_yield = F.coalesce(
        F.col("premium_yield_kg"),
        zero_yield,
    )

    return combined.select(
        "metric_date",
        "date_key",
        "farm_key",
        "farm_id",
        "year_week",
        total_yield.alias("total_yield_kg"),
        F.coalesce("harvest_count", F.lit(0)).cast("int").alias("harvest_count"),
        premium_yield.alias("premium_yield_kg"),
        (total_yield - premium_yield)
        .cast("decimal(18,3)")
        .alias("non_premium_yield_kg"),
        F.coalesce("energy_kwh", F.lit(0.0)).cast("double").alias("energy_kwh"),
        F.coalesce("reading_count", F.lit(0)).cast("long").alias("reading_count"),
        F.coalesce("anomaly_count", F.lit(0)).cast("long").alias("anomaly_count"),
        F.coalesce("in_range_count", F.lit(0)).cast("long").alias("in_range_count"),
        "last_sensor_reading_ts",
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    spark = build_spark_session(JOB_NAME, settings)

    try:
        quality_source = read_clickhouse_table(
            spark,
            settings,
            "fact_daily_farm_quality_metrics",
        )

        sensor_source = read_clickhouse_table(
            spark,
            settings,
            "fact_daily_sensor_metrics",
        )

        if quality_source.isEmpty() and sensor_source.isEmpty():
            logging.info("No daily source metrics; nothing to refresh")
            return

        quality = aggregate_quality(
            quality_source,
            read_clickhouse_table(
                spark,
                settings,
                "dim_quality_grade",
            ),
        )

        sensors = aggregate_sensors(
            sensor_source,
            read_clickhouse_table(
                spark,
                settings,
                "dim_sensor_type",
            ),
        )

        last_reading = aggregate_last_reading(
            read_clickhouse_table(
                spark,
                settings,
                "fact_sensor_readings",
            )
        )

        result = combine_metrics(
            quality,
            sensors,
            last_reading,
            read_clickhouse_table(
                spark,
                settings,
                "dim_date",
            ),
        )

        full_refresh_table(
            result,
            settings,
            TARGET_TABLE,
        )

        logging.info("Refreshed %s", TARGET_TABLE)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
