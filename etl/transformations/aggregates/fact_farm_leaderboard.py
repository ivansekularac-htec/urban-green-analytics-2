"""
Creates fact_farm_leaderboard from fact_daily_farm_metrics.

The aggregation calculates daily farm performance rankings based on:

- total production yield
- premium quality production share
- energy efficiency

The leaderboard combines individual metric rankings into a
composite score that represents overall farm performance.

Only records inside the configured aggregation refresh window
are processed.
"""

from common.clickhouse import read_clickhouse
from common.config import AGG_REFRESH_DAYS
from pyspark.sql import Window
from pyspark.sql.functions import (
    col,
    current_date,
    date_sub,
    dense_rank,
    lit,
    percent_rank,
    round,
    when,
)


def create_fact_farm_leaderboard(spark):
    """
    Creates farm leaderboard dataframe.

    The function:

    - reads daily farm metrics
    - filters data inside the refresh window
    - calculates quality and energy efficiency indicators
    - ranks farms by individual metrics
    - calculates a composite performance score
    - assigns final leaderboard ranking

    Returns
    -------
    DataFrame
        Farm leaderboard dataframe ready for loading into ClickHouse.
    """

    metrics = read_clickhouse(
        spark,
        "fact_daily_farm_metrics",
    )

    metrics = metrics.filter(
        col("metric_date")
        >= date_sub(
            current_date(),
            AGG_REFRESH_DAYS,
        )
    )

    premium_share = when(
        col("total_yield_kg") > 0,
        col("premium_yield_kg") / col("total_yield_kg"),
    ).otherwise(lit(0.0))

    energy_efficiency = when(
        col("total_yield_kg") > 0,
        col("energy_kwh") / col("total_yield_kg"),
    ).otherwise(lit(0.0))

    yield_window = Window.partitionBy("metric_date").orderBy(
        col("total_yield_kg").desc()
    )

    quality_window = Window.partitionBy("metric_date").orderBy(premium_share.desc())

    energy_window = Window.partitionBy("metric_date").orderBy(energy_efficiency.asc())

    ranked = (
        metrics.withColumn(
            "premium_yield_share",
            premium_share,
        )
        .withColumn(
            "energy_efficiency_kwh_per_kg",
            energy_efficiency,
        )
        .withColumn(
            "yield_rank",
            dense_rank().over(yield_window),
        )
        .withColumn(
            "quality_rank",
            dense_rank().over(quality_window),
        )
        .withColumn(
            "energy_rank",
            dense_rank().over(energy_window),
        )
        .withColumn(
            "_yield_score",
            1 - percent_rank().over(yield_window),
        )
        .withColumn(
            "_quality_score",
            1 - percent_rank().over(quality_window),
        )
        .withColumn(
            "_energy_score",
            1 - percent_rank().over(energy_window),
        )
        .withColumn(
            "composite_score",
            round(
                (col("_yield_score") + col("_quality_score") + col("_energy_score"))
                / 3
                * 100,
                6,
            ),
        )
    )

    composite_window = Window.partitionBy("metric_date").orderBy(
        col("composite_score").desc()
    )

    return ranked.withColumn(
        "composite_rank",
        dense_rank().over(composite_window),
    ).select(
        "metric_date",
        "date_key",
        "farm_key",
        "farm_id",
        col("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
        col("premium_yield_share").cast("double"),
        col("energy_efficiency_kwh_per_kg").cast("double"),
        col("yield_rank").cast("int"),
        col("quality_rank").cast("int"),
        col("energy_rank").cast("int"),
        col("composite_score").cast("double"),
        col("composite_rank").cast("int"),
    )
