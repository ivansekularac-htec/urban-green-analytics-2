"""Type-1 loader for dim_crop.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/postgres/crops/ + raw/postgres/crop_categories/
Target: urbangreen_dw.dim_crop
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import write_table
from common.jobs import run_job
from common.lake import read_postgres
from common.transforms import latest_by_key
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def _load(spark: SparkSession) -> None:
    """Load crops with denormalized category_name into dim_crop."""
    crops = read_postgres(spark, "crops")
    cats = read_postgres(spark, "crop_categories")
    if crops is None or cats is None:
        logger.info("no crops/crop_categories data in lake; skipping")
        return

    cats = latest_by_key(cats, "id").select(
        F.col("id").alias("category_id"),
        F.col("name").alias("category_name"),
    )

    out = (
        latest_by_key(crops, "id")
        .join(cats, "category_id", "left")
        .select(
            F.col("id").alias("crop_id"),
            F.col("name"),
            F.coalesce(F.col("description"), F.lit("")).alias("description"),
            F.col("category_id").alias("crop_category_id"),
            F.col("category_name"),
        )
    )
    write_table(out, "dim_crop")
    logger.info(f"dim_crop: wrote {out.count()} row(s)")


if __name__ == "__main__":
    run_job("load_dim_crop", _load)
