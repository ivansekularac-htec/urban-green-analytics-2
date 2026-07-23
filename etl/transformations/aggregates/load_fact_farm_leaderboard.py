"""Refresh loader for fact_farm_leaderboard.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Ranks farms over AGG_REFRESH_DAYS using fact_daily_farm_metrics FINAL.
Run after load_fact_daily_farm_metrics.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import read_sql, write_table
from common.constants import AGG_REFRESH_DAYS
from common.jobs import run_job
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def _load(spark: SparkSession) -> None:
    """Recompute the farm leaderboard snapshot and append."""
    days = AGG_REFRESH_DAYS

    farm_cur = F.broadcast(
        read_sql(
            spark,
            "SELECT farm_id, farm_key FROM dim_farm FINAL WHERE is_current = 1",
        )
    )

    m = read_sql(
        spark,
        "SELECT farm_id, total_yield_kg, premium_yield_kg, energy_kwh "
        f"FROM fact_daily_farm_metrics FINAL "
        f"WHERE metric_date >= today() - {days}",
    )

    agg = m.groupBy("farm_id").agg(
        F.sum("total_yield_kg").alias("total_yield_kg"),
        F.sum("premium_yield_kg").alias("premium_yield_kg"),
        F.sum("energy_kwh").alias("energy_kwh"),
    )

    total = F.col("total_yield_kg")
    agg = agg.withColumn(
        "premium_yield_share",
        F.when(total > 0, F.col("premium_yield_kg") / total).otherwise(0.0),
    ).withColumn(
        "energy_efficiency_kwh_per_kg",
        F.when(total > 0, F.col("energy_kwh") / total).otherwise(0.0),
    )

    agg = (
        agg.withColumn(
            "yield_rank",
            F.rank().over(Window.orderBy(F.col("total_yield_kg").desc())),
        )
        .withColumn(
            "quality_rank",
            F.rank().over(Window.orderBy(F.col("premium_yield_share").desc())),
        )
        .withColumn(
            "energy_rank",
            F.rank().over(Window.orderBy(F.col("energy_efficiency_kwh_per_kg").asc())),
        )
    )
    agg = agg.withColumn(
        "composite_score",
        (F.col("yield_rank") + F.col("quality_rank") + F.col("energy_rank")) / 3.0,
    ).withColumn(
        "composite_rank",
        F.rank().over(Window.orderBy(F.col("composite_score").asc())),
    )

    out = (
        agg.join(farm_cur, "farm_id")
        .withColumn("metric_date", F.current_date())
        .withColumn("date_key", F.date_format(F.current_date(), "yyyyMMdd").cast("int"))
        .select(
            "metric_date",
            "date_key",
            "farm_key",
            "farm_id",
            F.col("total_yield_kg").cast("decimal(18,3)"),
            F.col("premium_yield_share"),
            F.col("energy_efficiency_kwh_per_kg"),
            F.col("yield_rank").cast("int"),
            F.col("quality_rank").cast("int"),
            F.col("energy_rank").cast("int"),
            F.col("composite_score"),
            F.col("composite_rank").cast("int"),
        )
    )

    write_table(out, "fact_farm_leaderboard")
    logger.info(f"fact_farm_leaderboard: refreshed over last {days} day(s)")


if __name__ == "__main__":
    run_job("load_fact_farm_leaderboard", _load)
