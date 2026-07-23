"""Refresh loader for fact_daily_farm_quality_metrics.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

One row per farm x quality_grade x day over AGG_REFRESH_DAYS, from
fact_harvests FINAL.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import read_sql, write_table
from common.constants import AGG_REFRESH_DAYS
from common.jobs import run_job
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def _load(spark: SparkSession) -> None:
    """Recompute daily farm-quality metrics for the refresh window and append."""
    days = AGG_REFRESH_DAYS

    datemap = F.broadcast(read_sql(spark, "SELECT date_key, full_date FROM dim_date"))
    farm_cur = F.broadcast(
        read_sql(
            spark,
            "SELECT farm_id, farm_key FROM dim_farm FINAL WHERE is_current = 1",
        )
    )

    harv = read_sql(
        spark,
        "SELECT farm_id, date_key, quality_grade_id, weight_kg "
        f"FROM fact_harvests FINAL WHERE harvest_date >= today() - {days}",
    )

    out = (
        harv.groupBy("farm_id", "date_key", "quality_grade_id")
        .agg(
            F.sum("weight_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.count("*").cast("int").alias("harvest_count"),
        )
        .join(datemap, "date_key")
        .join(farm_cur, "farm_id")
        .select(
            F.col("full_date").alias("metric_date"),
            F.col("date_key"),
            F.col("farm_key"),
            F.col("farm_id"),
            F.col("quality_grade_id"),
            F.col("total_yield_kg"),
            F.col("harvest_count"),
        )
    )

    write_table(out, "fact_daily_farm_quality_metrics")
    print(f"fact_daily_farm_quality_metrics: refreshed last {days} day(s)")


if __name__ == "__main__":
    run_job("load_fact_daily_farm_quality_metrics", _load)
