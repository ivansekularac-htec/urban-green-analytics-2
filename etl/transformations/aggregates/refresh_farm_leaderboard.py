"""Refresh daily farm rankings and composite leaderboard scores."""

import logging
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

JOB_NAME = "refresh_farm_leaderboard"
SOURCE_TABLE = "fact_daily_farm_metrics"
TARGET_TABLE = "fact_farm_leaderboard"


def build_leaderboard(
    dataframe: DataFrame,
) -> DataFrame:
    total_yield = F.col("total_yield_kg").cast("double")

    premium_share = F.when(
        total_yield > 0,
        F.col("premium_yield_kg").cast("double") / total_yield,
    ).otherwise(0.0)

    energy_efficiency = F.when(
        total_yield > 0,
        F.col("energy_kwh") / total_yield,
    ).otherwise(0.0)

    energy_sort_value = F.when(
        total_yield > 0,
        energy_efficiency,
    ).otherwise(float("inf"))

    yield_window = Window.partitionBy("metric_date").orderBy(
        F.col("total_yield_kg").desc()
    )

    quality_window = Window.partitionBy("metric_date").orderBy(premium_share.desc())

    energy_window = Window.partitionBy("metric_date").orderBy(energy_sort_value.asc())

    ranked = (
        dataframe.withColumn(
            "premium_yield_share",
            premium_share,
        )
        .withColumn(
            "energy_efficiency_kwh_per_kg",
            energy_efficiency,
        )
        .withColumn(
            "yield_rank",
            F.dense_rank().over(yield_window),
        )
        .withColumn(
            "quality_rank",
            F.dense_rank().over(quality_window),
        )
        .withColumn(
            "energy_rank",
            F.dense_rank().over(energy_window),
        )
        .withColumn(
            "_yield_score",
            1.0 - F.percent_rank().over(yield_window),
        )
        .withColumn(
            "_quality_score",
            1.0 - F.percent_rank().over(quality_window),
        )
        .withColumn(
            "_energy_score",
            1.0 - F.percent_rank().over(energy_window),
        )
        .withColumn(
            "composite_score",
            F.round(
                (
                    F.col("_yield_score")
                    + F.col("_quality_score")
                    + F.col("_energy_score")
                )
                / 3.0
                * 100.0,
                6,
            ),
        )
    )

    composite_window = Window.partitionBy("metric_date").orderBy(
        F.col("composite_score").desc()
    )

    return ranked.withColumn(
        "composite_rank",
        F.dense_rank().over(composite_window),
    ).select(
        "metric_date",
        "date_key",
        "farm_key",
        "farm_id",
        F.col("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
        F.col("premium_yield_share").cast("double"),
        F.col("energy_efficiency_kwh_per_kg").cast("double"),
        F.col("yield_rank").cast("int"),
        F.col("quality_rank").cast("int"),
        F.col("energy_rank").cast("int"),
        F.col("composite_score").cast("double"),
        F.col("composite_rank").cast("int"),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    spark = build_spark_session(JOB_NAME, settings)

    try:
        source = read_clickhouse_table(
            spark,
            settings,
            SOURCE_TABLE,
        )

        if source.isEmpty():
            logging.info(
                "No rows in %s; nothing to refresh",
                SOURCE_TABLE,
            )
            return

        result = build_leaderboard(source)

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
