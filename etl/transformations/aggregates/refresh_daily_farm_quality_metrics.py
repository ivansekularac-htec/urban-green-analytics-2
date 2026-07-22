"""Refresh daily farm quality metrics within the configured date window."""

import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

ETL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETL_ROOT))

from transformations.common.clickhouse import read_clickhouse_table
from transformations.common.config import load_settings
from transformations.common.spark_session import build_spark_session
from transformations.common.staging import full_refresh_table

JOB_NAME = "refresh_daily_farm_quality_metrics"
SOURCE_TABLE = "fact_harvests"
TARGET_TABLE = "fact_daily_farm_quality_metrics"

DEFAULT_REFRESH_DAYS = 7

TARGET_COLUMNS = [
    "metric_date",
    "date_key",
    "farm_key",
    "farm_id",
    "quality_grade_id",
    "total_yield_kg",
    "harvest_count",
]


def latest_harvests(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy(
        "harvest_id",
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
        "quality_grade_id",
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


def aggregate_quality_metrics(
    dataframe: DataFrame,
) -> DataFrame:
    return (
        dataframe.groupBy(
            F.col("harvest_date").alias("metric_date"),
            "date_key",
            "farm_key",
            "farm_id",
            "quality_grade_id",
        )
        .agg(
            F.sum("weight_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.count(F.lit(1)).cast("int").alias("harvest_count"),
        )
        .select(*TARGET_COLUMNS)
    )


def determine_refresh_start(
    facts: DataFrame,
    target_is_empty: bool,
    refresh_days: int,
):
    date_range = facts.agg(
        F.min("harvest_date").alias("min_date"),
        F.max("harvest_date").alias("max_date"),
    ).first()

    if target_is_empty:
        return date_range["min_date"]

    return date_range["max_date"] - timedelta(days=refresh_days - 1)


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
        facts = latest_harvests(
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

        refreshed = aggregate_quality_metrics(
            facts.filter(F.col("harvest_date") >= F.lit(refresh_start))
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
