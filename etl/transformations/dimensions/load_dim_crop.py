"""
Read crop source data from MinIO, transform it, and load the dim_crop
warehouse table in ClickHouse.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp, lit
from transformations.common import create_spark, read_raw_table, write_clickhouse

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def transform_dim_crop(
    crops_df: DataFrame,
    categories_df: DataFrame,
) -> DataFrame:
    """
    Build the dim_crop warehouse dimension by joining crops with their
    category metadata.
    """

    return crops_df.join(
        categories_df,
        crops_df.category_id == categories_df.id,
        "left",
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
    """
    Load the dim_crop dimension from raw PostgreSQL snapshots into ClickHouse.
    """
    spark = create_spark("load_dim_crop")

    try:
        crops_df = read_raw_table(
            spark,
            MINIO_STAGING_BUCKET,
            "crops",
        )

        categories_df = read_raw_table(
            spark,
            MINIO_STAGING_BUCKET,
            "crop_categories",
        )

        dim_crop_df = transform_dim_crop(
            crops_df,
            categories_df,
        )

        # Write to ClickHouse. ReplacingMergeTree ensures repeated runs converge
        # to the latest version of each crop.
        write_clickhouse(
            dim_crop_df,
            "dim_crop",
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
