"""Refresh loader for fact_daily_farm_metrics.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Recomputes the last AGG_REFRESH_DAYS days from fact tables with FINAL so late
edits inside the window are reflected on every run. No watermark — full window
refresh by design.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import read_sql, write_table
from common.constants import AGG_REFRESH_DAYS
from common.jobs import run_job
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def _load(spark: SparkSession) -> None:
    """Recompute daily farm metrics for the refresh window and append."""
    days = AGG_REFRESH_DAYS

    datemap = F.broadcast(
        read_sql(spark, "SELECT date_key, full_date, year_week FROM dim_date")
    )
    farm_cur = F.broadcast(
        read_sql(
            spark,
            "SELECT farm_id, farm_key FROM dim_farm FINAL WHERE is_current = 1",
        )
    )

    premium_ids = [
        r["quality_grade_id"]
        for r in read_sql(
            spark,
            "SELECT quality_grade_id FROM dim_quality_grade FINAL WHERE is_premium = 1",
        ).collect()
    ]
    energy_rows = read_sql(
        spark,
        "SELECT sensor_type_key FROM dim_sensor_type FINAL "
        "WHERE is_current = 1 AND name = 'Energy Usage'",
    ).collect()
    if not energy_rows:
        logger.warning("no current dim_sensor_type named 'Energy Usage'; energy_kwh=0")
        energy_key = -1
    else:
        energy_key = energy_rows[0]["sensor_type_key"]

    harv = read_sql(
        spark,
        "SELECT farm_id, date_key, quality_grade_id, weight_kg "
        f"FROM fact_harvests FINAL WHERE harvest_date >= today() - {days}",
    )
    sens = read_sql(
        spark,
        "SELECT farm_id, date_key, sensor_type_key, value, is_anomaly, reading_ts "
        f"FROM fact_sensor_readings FINAL WHERE reading_date >= today() - {days}",
    )

    premium = (
        F.col("quality_grade_id").isin(premium_ids) if premium_ids else F.lit(False)
    )
    harvest_agg = harv.groupBy("farm_id", "date_key").agg(
        F.sum("weight_kg").alias("total_yield_kg"),
        F.count("*").alias("harvest_count"),
        F.sum(F.when(premium, F.col("weight_kg")).otherwise(0)).alias(
            "premium_yield_kg"
        ),
    )
    sensor_agg = sens.groupBy("farm_id", "date_key").agg(
        F.sum(
            F.when(F.col("sensor_type_key") == energy_key, F.col("value")).otherwise(
                0.0
            )
        ).alias("energy_kwh"),
        F.count("*").alias("reading_count"),
        F.sum("is_anomaly").alias("anomaly_count"),
        F.max("reading_ts").alias("last_sensor_reading_ts"),
    )

    out = (
        harvest_agg.join(sensor_agg, ["farm_id", "date_key"], "full_outer")
        .join(datemap, "date_key")
        .join(farm_cur, "farm_id")
        .select(
            F.col("full_date").alias("metric_date"),
            F.col("date_key"),
            F.col("farm_key"),
            F.col("farm_id"),
            F.col("year_week"),
            F.coalesce(F.col("total_yield_kg"), F.lit(0))
            .cast("decimal(18,3)")
            .alias("total_yield_kg"),
            F.coalesce(F.col("harvest_count"), F.lit(0))
            .cast("int")
            .alias("harvest_count"),
            F.coalesce(F.col("premium_yield_kg"), F.lit(0))
            .cast("decimal(18,3)")
            .alias("premium_yield_kg"),
            (
                F.coalesce(F.col("total_yield_kg"), F.lit(0))
                - F.coalesce(F.col("premium_yield_kg"), F.lit(0))
            )
            .cast("decimal(18,3)")
            .alias("non_premium_yield_kg"),
            F.coalesce(F.col("energy_kwh"), F.lit(0.0)).alias("energy_kwh"),
            F.coalesce(F.col("reading_count"), F.lit(0))
            .cast("long")
            .alias("reading_count"),
            F.coalesce(F.col("anomaly_count"), F.lit(0))
            .cast("long")
            .alias("anomaly_count"),
            (
                F.coalesce(F.col("reading_count"), F.lit(0))
                - F.coalesce(F.col("anomaly_count"), F.lit(0))
            )
            .cast("long")
            .alias("in_range_count"),
            F.col("last_sensor_reading_ts"),
        )
    )

    write_table(out, "fact_daily_farm_metrics")
    logger.info(f"fact_daily_farm_metrics: refreshed last {days} day(s)")


if __name__ == "__main__":
    run_job("load_fact_daily_farm_metrics", _load)
