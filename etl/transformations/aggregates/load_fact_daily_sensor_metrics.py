"""Refresh loader for fact_daily_sensor_metrics.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

One row per farm x sensor_type x day over AGG_REFRESH_DAYS, from
fact_sensor_readings FINAL.
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
    """Recompute daily sensor metrics for the refresh window and append."""
    days = AGG_REFRESH_DAYS

    datemap = F.broadcast(read_sql(spark, "SELECT date_key, full_date FROM dim_date"))
    farm_cur = F.broadcast(
        read_sql(
            spark,
            "SELECT farm_id, farm_key FROM dim_farm FINAL WHERE is_current = 1",
        )
    )

    sens = read_sql(
        spark,
        "SELECT farm_id, date_key, sensor_type_key, value, is_anomaly "
        f"FROM fact_sensor_readings FINAL WHERE reading_date >= today() - {days}",
    )

    out = (
        sens.groupBy("farm_id", "date_key", "sensor_type_key")
        .agg(
            F.count("*").cast("long").alias("reading_count"),
            F.sum("value").alias("sum_value"),
            F.min("value").alias("min_value"),
            F.max("value").alias("max_value"),
            F.sum("is_anomaly").cast("long").alias("anomaly_count"),
        )
        .withColumn(
            "in_range_count",
            (F.col("reading_count") - F.col("anomaly_count")).cast("long"),
        )
        .join(datemap, "date_key")
        .join(farm_cur, "farm_id")
        .select(
            F.col("full_date").alias("metric_date"),
            F.col("date_key"),
            F.col("farm_key"),
            F.col("farm_id"),
            F.col("sensor_type_key"),
            F.col("reading_count"),
            F.col("sum_value"),
            F.col("min_value"),
            F.col("max_value"),
            F.col("anomaly_count"),
            F.col("in_range_count"),
        )
    )

    write_table(out, "fact_daily_sensor_metrics")
    print(f"fact_daily_sensor_metrics: refreshed last {days} day(s)")


if __name__ == "__main__":
    run_job("load_fact_daily_sensor_metrics", _load)
