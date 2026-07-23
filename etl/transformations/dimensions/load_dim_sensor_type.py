"""SCD2 loader for dim_sensor_type.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/sensor_types/
Target: urbangreen_dw.dim_sensor_type

sensor_type_key is left to ClickHouse DEFAULT.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import write_table
from common.jobs import run_job
from common.lake import read_postgres
from common.transforms import build_scd2
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def _load(spark: SparkSession) -> None:
    """Build sensor-type SCD2 versions and write them to dim_sensor_type."""
    raw = read_postgres(spark, "sensor_types")
    if raw is None:
        logger.info("no sensor_types data in lake; skipping")
        return

    out = build_scd2(raw, "id").select(
        F.col("id").alias("sensor_type_id"),
        F.col("name"),
        F.col("unit"),
        F.coalesce(F.col("description"), F.lit("")).alias("description"),
        F.col("optimal_min").cast("double"),
        F.col("optimal_max").cast("double"),
        F.col("valid_from"),
        F.col("valid_to"),
        F.col("is_current"),
        F.col("_version"),
    )
    write_table(out, "dim_sensor_type")
    logger.info("dim_sensor_type: load complete")


if __name__ == "__main__":
    run_job("load_dim_sensor_type", _load)
