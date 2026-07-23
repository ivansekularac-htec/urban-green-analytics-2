"""SCD2 loader for dim_sensor.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/sensors/
Target: urbangreen_dw.dim_sensor

Resolves farm_key and sensor_type_key from current SCD2 rows.
Run after load_dim_farm and load_dim_sensor_type.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import read_sql, write_table
from common.jobs import run_job
from common.lake import read_postgres
from common.transforms import build_scd2
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def _load(spark: SparkSession) -> None:
    """Build sensor SCD2 versions and write them to dim_sensor."""
    sensors = read_postgres(spark, "sensors")
    if sensors is None:
        print("no sensors data in lake; skipping")
        return

    farm_keys = read_sql(
        spark,
        "SELECT farm_id, farm_key FROM dim_farm FINAL WHERE is_current = 1",
    )
    st_keys = read_sql(
        spark,
        "SELECT sensor_type_id, sensor_type_key FROM dim_sensor_type FINAL "
        "WHERE is_current = 1",
    )

    out = (
        build_scd2(sensors, "id")
        .join(F.broadcast(farm_keys), "farm_id", "left")
        .join(F.broadcast(st_keys), "sensor_type_id", "left")
        .select(
            F.col("id").alias("sensor_id"),
            F.coalesce(F.col("farm_key"), F.lit(0)).alias("farm_key"),
            F.coalesce(F.col("sensor_type_key"), F.lit(0)).alias("sensor_type_key"),
            F.col("serial_number"),
            F.col("status"),
            F.timestamp_seconds("installed_at").alias("installed_at"),
            F.col("valid_from"),
            F.col("valid_to"),
            F.col("is_current"),
            F.col("_version"),
        )
    )
    write_table(out, "dim_sensor")
    print("dim_sensor: load complete")


if __name__ == "__main__":
    run_job("load_dim_sensor", _load)
