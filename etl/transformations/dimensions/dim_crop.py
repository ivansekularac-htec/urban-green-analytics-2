"""
Load the dim_crop warehouse dimension from incremental raw data.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, current_timestamp, lit
from transformations.common import (
    create_spark,
    read_clickhouse,
    read_latest_batch,
    write_clickhouse,
)

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


def read_current_dim_crop(
    spark,
) -> DataFrame:
    """
    Read the current ClickHouse state of dim_crop.

    FINAL makes ReplacingMergeTree return the latest version.
    """

    return read_clickhouse(
        spark,
        """
        (
            SELECT *
            FROM dim_crop FINAL
        ) AS dim_crop
        """,
    )


def get_category_affected_crops(
    current_dim_crop_df: DataFrame,
    changed_categories_df: DataFrame,
) -> DataFrame:
    """
    Find existing crops whose category was updated.
    """

    return current_dim_crop_df.join(
        changed_categories_df,
        current_dim_crop_df.crop_category_id == changed_categories_df.id,
        "inner",
    ).select(
        current_dim_crop_df.crop_id,
    )


def main():

    spark = create_spark(
        "load_dim_crop",
    )

    try:
        changed_crops_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "crops",
        )

        changed_categories_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "crop_categories",
        )

        current_dim_crop_df = read_current_dim_crop(
            spark,
        )

        # Find crops affected by category changes.
        category_affected_crop_ids = get_category_affected_crops(
            current_dim_crop_df,
            changed_categories_df,
        )

        # Read old crop records and rebuild them with new category names.
        category_affected_crops_df = current_dim_crop_df.join(
            category_affected_crop_ids,
            "crop_id",
            "inner",
        ).select(
            "crop_id",
            "name",
            "description",
            col("crop_category_id").alias("category_id"),
        )

        # Combine:
        # - directly changed crops
        # - crops affected by category changes
        crops_to_update_df = (
            changed_crops_df.select(
                "id",
                "name",
                "description",
                "category_id",
            )
            .unionByName(
                category_affected_crops_df.select(
                    col("crop_id").alias("id"),
                    "name",
                    "description",
                    "category_id",
                )
            )
            .dropDuplicates(["id"])
        )

        dim_crop_updates_df = transform_dim_crop(
            crops_to_update_df,
            changed_categories_df.unionByName(
                current_dim_crop_df.select(
                    col("crop_category_id").alias("id"),
                    col("category_name").alias("name"),
                )
            ),
        )

        write_clickhouse(
            dim_crop_updates_df,
            "dim_crop",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
