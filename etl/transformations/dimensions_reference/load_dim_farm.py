"""
Read crop source data from MinIO, transform it, and load the dim_crop
warehouse table in ClickHouse.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import lit
from transformations.common import (
    create_spark,
    epoch_to_timestamp,
    read_raw_table,
    write_clickhouse,
)

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def transform_dim_farm(
    farm_df: DataFrame,
    infrastructure_type_df: DataFrame,
    growing_system_type_df: DataFrame,
) -> DataFrame:
    """
    Build the dim_crop warehouse dimension by joining crops with their
    category metadata.
    """

    return (
        farm_df.join(
            infrastructure_type_df,
            farm_df.infrastructure_type_id == infrastructure_type_df.id,
            "left",
        )
        .join(
            growing_system_type_df,
            farm_df.growing_system_type_id == growing_system_type_df.id,
            "left",
        )
        .select(
            farm_df.id.alias("farm_id"),
            farm_df.name,
            farm_df.city,
            farm_df.size_m2,
            farm_df.growing_beds_count,
            farm_df.status,
            farm_df.infrastructure_type_id,
            infrastructure_type_df.name.alias("infrastructure_type_name"),
            farm_df.growing_system_type_id,
            growing_system_type_df.name.alias("growing_system_type_name"),
            epoch_to_timestamp(farm_df.created_at).alias("created_at"),
            lit(1).alias("is_current"),
            farm_df.updated_at.alias("_version"),
        )
    )


def main():
    """
    Load the dim_crop dimension from raw PostgreSQL snapshots into ClickHouse.
    """
    spark = create_spark("load_dim_farm")

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
