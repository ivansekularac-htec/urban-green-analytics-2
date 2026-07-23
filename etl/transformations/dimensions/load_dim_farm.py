"""SCD2 loader for dim_farm.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/farms/ (+ infrastructure / growing-system lookups)
Target: urbangreen_dw.dim_farm

farm_key is left to ClickHouse DEFAULT cityHash64(farm_id, valid_from).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import write_table
from common.jobs import run_job
from common.lake import read_postgres
from common.transforms import build_scd2, latest_by_key
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def _load(spark: SparkSession) -> None:
    """Build farm SCD2 versions and write them to dim_farm."""
    farms = read_postgres(spark, "farms")
    if farms is None:
        print("no farms data in lake; skipping")
        return

    infra_raw = read_postgres(spark, "farm_infrastructure_types")
    gs_raw = read_postgres(spark, "growing_system_types")
    if infra_raw is None or gs_raw is None:
        print("missing farm lookup tables in lake; skipping")
        return

    infra = latest_by_key(infra_raw, "id").select(
        F.col("id").alias("infrastructure_type_id"),
        F.col("name").alias("infrastructure_type_name"),
    )
    gs = latest_by_key(gs_raw, "id").select(
        F.col("id").alias("growing_system_type_id"),
        F.col("name").alias("growing_system_type_name"),
    )

    out = (
        build_scd2(farms, "id")
        .join(F.broadcast(infra), "infrastructure_type_id", "left")
        .join(F.broadcast(gs), "growing_system_type_id", "left")
        .select(
            F.col("id").alias("farm_id"),
            F.col("name"),
            F.col("city"),
            F.col("size_m2").cast("decimal(10,3)"),
            F.col("growing_beds_count").cast("int"),
            F.col("status"),
            F.col("infrastructure_type_id"),
            F.col("infrastructure_type_name"),
            F.col("growing_system_type_id"),
            F.col("growing_system_type_name"),
            F.col("valid_from"),
            F.col("valid_to"),
            F.col("is_current"),
            F.col("_version"),
        )
    )
    write_table(out, "dim_farm")
    print("dim_farm: load complete")


if __name__ == "__main__":
    run_job("load_dim_farm", _load)
