"""
Load the dim_crop warehouse dimension from incremental raw data.
"""

import os

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql.functions import col, current_timestamp, lit, row_number
from transformations.common import (
    create_spark,
    list_batches,
    read_parquet,
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


def read_current_snapshot(
    spark: SparkSession,
    bucket: str,
    table_name: str,
    primary_key: str = "id",
    version_column: str = "updated_at",
) -> DataFrame:
    """
    Reconstruct the current table state from all incremental batches.

    Airflow stores only changed rows in each batch, so the latest batch is
    not necessarily a complete snapshot. This helper reads every available
    batch and keeps only the newest version of each primary key.

    Example:

        batch1
        id=1
        id=2

        batch2
        id=2 (updated)

        result
        id=1
        id=2 (updated)
    """

    base_path = f"s3a://{bucket}/raw/postgres/{table_name}/"

    batches = list_batches(
        spark,
        base_path,
    )

    paths = [f"{base_path}{batch}" for batch in batches]

    df = read_parquet(
        spark,
        *paths,
    )

    window = Window.partitionBy(primary_key).orderBy(col(version_column).desc())

    return (
        df.withColumn(
            "_row_number",
            row_number().over(window),
        )
        .filter(
            col("_row_number") == 1,
        )
        .drop("_row_number")
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
