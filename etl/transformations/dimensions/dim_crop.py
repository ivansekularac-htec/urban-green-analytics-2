"""
Load the dim_crop warehouse dimension from incremental raw data.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp, lit
from transformations.common import create_spark, read_current_snapshot, write_clickhouse

MINIO_STAGING_BUCKET = os.environ.get(
    "MINIO_STAGING_BUCKET",
    "staging",
)


def transform_dim_crop(
    crops_df: DataFrame,
    categories_df: DataFrame,
) -> DataFrame:
    """
    Build dim_crop rows from changed crops and categories.
    """

    return crops_df.join(
        categories_df,
        crops_df.category_id == categories_df.id,
        "inner",
    ).select(
        crops_df.id.alias("crop_id"),
        crops_df.name,
        crops_df.description,
        crops_df.category_id.alias("crop_category_id"),
        categories_df.name.alias("category_name"),
        lit(0).alias("is_high_value"),
        current_timestamp().alias("_loaded_at"),
    )


def main():

    spark = create_spark("load_dim_crop")

    try:
        crops_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "crops",
        )

        categories_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "crop_categories",
        )

        dim_crop_df = transform_dim_crop(
            crops_df,
            categories_df,
        )

        write_clickhouse(
            dim_crop_df,
            "dim_crop",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
