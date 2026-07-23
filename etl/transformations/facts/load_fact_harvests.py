"""Incremental loader for fact_harvests.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/harvests/
Target: urbangreen_dw.fact_harvests

Source has no distinct harvest timestamp column (confirmed against
``infra/postgres/init/01_schema.sql`` and the API Harvest schema); ``created_at``
is the harvest event time used for ``harvested_at`` / date_key / time_key.

Reads only rows with updated_at greater than the last successful watermark.
Advances watermarks only after the JDBC write succeeds, and only when every
row resolved farm_key (otherwise the same slice is replayed).

Run after load_dim_farm.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import read_sql, write_table
from common.jobs import run_job
from common.lake_incremental import read_postgres_since
from common.transforms import latest_by_key, with_date_time_keys
from common.watermarks import get_watermark, set_watermark
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)

JOB = "fact_harvests"


def _load(spark: SparkSession) -> None:
    """Load new/changed harvests since the last watermark into fact_harvests."""
    wm = get_watermark(spark, JOB)
    raw = read_postgres_since(spark, "harvests", wm)
    if raw is None:
        logger.info(f"no new harvest run windows since watermark={wm}; skipping")
        return
    slice_ = raw.filter(F.col("updated_at") > wm)
    latest = latest_by_key(slice_, "id", "updated_at").cache()

    stats = latest.agg(
        F.max("updated_at").alias("hi"),
        F.count("*").alias("cnt"),
    ).collect()[0]
    new_wm, cnt = stats["hi"], int(stats["cnt"])

    if cnt == 0:
        latest.unpersist()
        logger.info(f"no new rows since watermark={wm}; skipping")
        return

    farm_dim = read_sql(
        spark,
        "SELECT farm_id, farm_key, valid_from, valid_to FROM dim_farm FINAL",
    )

    h = latest.withColumn("harvested_at", F.timestamp_seconds("created_at")).withColumn(
        "harvest_date", F.to_date("harvested_at")
    )
    h = with_date_time_keys(h, "harvested_at")

    joined = h.alias("h").join(
        F.broadcast(farm_dim).alias("f"),
        (F.col("h.farm_id") == F.col("f.farm_id"))
        & (F.col("h.harvested_at") >= F.col("f.valid_from"))
        & (F.col("h.harvested_at") < F.col("f.valid_to")),
        "left",
    )

    out = joined.select(
        F.col("h.id").alias("harvest_key"),
        F.col("h.id").alias("harvest_id"),
        F.coalesce(F.col("f.farm_key"), F.lit(0)).alias("farm_key"),
        F.col("h.farm_id"),
        F.col("h.crop_id"),
        F.col("h.quality_grade_id"),
        F.col("h.date_key"),
        F.col("h.time_key"),
        F.col("h.harvested_at"),
        F.col("h.harvest_date"),
        F.col("h.weight_kg").cast("decimal(10,3)"),
    ).cache()

    unresolved = out.filter(F.col("farm_key") == 0).count()

    write_table(out, "fact_harvests")
    latest.unpersist()

    if unresolved > 0:
        out.unpersist()
        logger.warning(
            f"fact_harvests: wrote {cnt} rows but {unresolved} unresolved "
            f"farm_key(s); watermark left at {wm} — re-run after load_dim_farm"
        )
        return

    set_watermark(spark, JOB, int(new_wm), cnt)
    out.unpersist()
    logger.info(f"fact_harvests: loaded {cnt} rows, watermark {wm} -> {new_wm}")


if __name__ == "__main__":
    run_job("load_fact_harvests", _load)
