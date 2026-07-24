"""Load dim_crop from the raw Postgres crops and crop_categories extracts.

Type 1 dimension: one current row per crop. The category name is denormalized
onto the crop so dashboards group by category without a second join, which is
what the star schema trades storage for.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse
from common.spark import build_spark, read_raw_postgres
from common.transform import latest_per_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "crops"
CATEGORY_TABLE = "crop_categories"
TARGET_TABLE = "dim_crop"


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        raw_crops = read_raw_postgres(spark, SOURCE_TABLE)
        if raw_crops is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        crops = latest_per_key(raw_crops, "id").select(
            F.col("id").cast("long").alias("crop_id"),
            F.col("name").cast("string").alias("name"),
            F.coalesce(F.col("description"), F.lit("")).cast("string").alias("description"),
            F.col("category_id").cast("long").alias("crop_category_id"),
        )

        # Left join on purpose: a crop whose category has not reached the raw
        # zone yet still belongs in the dimension, only without its category
        # name. An inner join would drop the crop entirely, and every fact row
        # pointing at it would then join to nothing.
        raw_categories = read_raw_postgres(spark, CATEGORY_TABLE)
        if raw_categories is None:
            logger.warning(f"no {CATEGORY_TABLE} extract; category names stay empty")
            enriched = crops.withColumn("category_name", F.lit(""))
        else:
            categories = latest_per_key(raw_categories, "id").select(
                F.col("id").cast("long").alias("crop_category_id"),
                F.col("name").cast("string").alias("category_name"),
            )
            enriched = crops.join(categories, on="crop_category_id", how="left")

        target = enriched.select(
            "crop_id",
            "name",
            "description",
            "crop_category_id",
            F.coalesce(F.col("category_name"), F.lit("")).alias("category_name"),
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
