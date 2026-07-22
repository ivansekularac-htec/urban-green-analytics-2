"""Load the latest crop and category attributes into dim_crop."""

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

ETL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETL_ROOT))


from transformations.common.config import load_settings
from transformations.common.lake_reader import read_postgres_table
from transformations.common.spark_session import build_spark_session
from transformations.common.staging import full_refresh_table

TARGET_TABLE = "dim_crop"


def latest_by_id(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy("id").orderBy(F.col("updated_at").desc())

    return (
        dataframe.withColumn("_row_number", F.row_number().over(window))
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )


def transform_crops(
    crops: DataFrame,
    categories: DataFrame,
) -> DataFrame:
    crops = latest_by_id(crops).alias("crop")

    categories = (
        latest_by_id(categories)
        .select(
            F.col("id").alias("category_id"),
            F.trim("name").alias("category_name"),
        )
        .alias("category")
    )

    category_name = F.col("category.category_name")

    return crops.join(
        categories,
        F.col("crop.category_id") == F.col("category.category_id"),
        "left",
    ).select(
        F.col("crop.id").cast("long").alias("crop_id"),
        F.trim("crop.name").alias("name"),
        F.coalesce(
            F.col("crop.description"),
            F.lit(""),
        ).alias("description"),
        F.col("crop.category_id").cast("long").alias("crop_category_id"),
        F.col("category.category_name").alias("category_name"),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    spark = build_spark_session(TARGET_TABLE, settings)

    try:
        crops = read_postgres_table(
            spark,
            settings,
            "crops",
        )

        categories = read_postgres_table(
            spark,
            settings,
            "crop_categories",
        )

        result = transform_crops(
            crops,
            categories,
        )

        full_refresh_table(
            result,
            settings,
            TARGET_TABLE,
        )

        logging.info("Loaded %s", TARGET_TABLE)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
