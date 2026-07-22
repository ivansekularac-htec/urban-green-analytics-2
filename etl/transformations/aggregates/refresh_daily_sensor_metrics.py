"""Refresh daily sensor metrics within the configured date window."""

import logging
import os
import sys
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

ETL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETL_ROOT))

from transformations.common.clickhouse import read_clickhouse_table
from transformations.common.config import load_settings
from transformations.common.spark_session import build_spark_session
from transformations.common.staging import full_refresh_table

JOB_NAME = "refresh_daily_sensor_metrics"
SOURCE_TABLE = "fact_sensor_readings"
TARGET_TABLE = "fact_daily_sensor_metrics"

DEFAULT_REFRESH_DAYS = 7

TARGET_COLUMNS = [
    "metric_date",
    "date_key",
    "farm_key",
    "farm_id",
    "sensor_type_key",
    "reading_count",
    "sum_value",
    "min_value",
    "max_value",
    "anomaly_count",
    "in_range_count",
]


def latest_sensor_readings(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy(
        "reading_key",
    ).orderBy(
        F.col("_loaded_at").desc(),
    )

    return (
        dataframe.withColumn(
            "_row_number",
            F.row_number().over(window),
        )
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )


def latest_target_rows(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy(
        "metric_date",
        "farm_id",
        "sensor_type_key",
        "farm_key",
    ).orderBy(
        F.col("_loaded_at").desc(),
    )

    return (
        dataframe.withColumn(
            "_row_number",
            F.row_number().over(window),
        )
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )


def aggregate_sensor_metrics(
    dataframe: DataFrame,
) -> DataFrame:
    return (
        dataframe.groupBy(
            F.col("reading_date").alias("metric_date"),
            "date_key",
            "farm_key",
            "farm_id",
            "sensor_type_key",
        )
        .agg(
            F.count(F.lit(1)).cast("long").alias("reading_count"),
            F.sum("value").cast("double").alias("sum_value"),
            F.min("value").cast("double").alias("min_value"),
            F.max("value").cast("double").alias("max_value"),
            F.sum("is_anomaly").cast("long").alias("anomaly_count"),
            F.sum(
                F.when(
                    F.col("is_anomaly") == 0,
                    1,
                ).otherwise(0)
            )
            .cast("long")
            .alias("in_range_count"),
        )
        .select(*TARGET_COLUMNS)
    )


def determine_refresh_start(
    facts: DataFrame,
    target_is_empty: bool,
    refresh_days: int,
):
    date_range = facts.agg(
        F.min("reading_date").alias("min_date"),
        F.max("reading_date").alias("max_date"),
    ).first()

    if target_is_empty:
        return date_range["min_date"]

    return date_range["max_date"] - (refresh_days - 1) * __import__(
        "datetime"
    ).timedelta(days=1)


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    refresh_days = int(
        os.getenv(
            "AGGREGATE_REFRESH_DAYS",
            str(DEFAULT_REFRESH_DAYS),
        )
    )

    if refresh_days < 1:
        raise ValueError("AGGREGATE_REFRESH_DAYS must be at least 1")

    settings = load_settings()
    spark = build_spark_session(JOB_NAME, settings)

    try:
        facts = latest_sensor_readings(
            read_clickhouse_table(
                spark,
                settings,
                SOURCE_TABLE,
            )
        ).cache()

        if facts.isEmpty():
            logging.info(
                "No rows in %s; nothing to refresh",
                SOURCE_TABLE,
            )
            return

        existing_target = read_clickhouse_table(
            spark,
            settings,
            TARGET_TABLE,
        ).cache()

        target_is_empty = existing_target.isEmpty()

        refresh_start = determine_refresh_start(
            facts,
            target_is_empty,
            refresh_days,
        )

        refreshed = aggregate_sensor_metrics(
            facts.filter(F.col("reading_date") >= F.lit(refresh_start))
        )

        if target_is_empty:
            result = refreshed
        else:
            historical = (
                latest_target_rows(existing_target)
                .filter(F.col("metric_date") < F.lit(refresh_start))
                .select(*TARGET_COLUMNS)
            )

            result = historical.unionByName(refreshed)

        full_refresh_table(
            result,
            settings,
            TARGET_TABLE,
        )

        logging.info(
            "Refreshed %s from %s",
            TARGET_TABLE,
            refresh_start,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
