"""
Load the dim_farm warehouse dimension from raw PostgreSQL snapshots.
"""

import os
import time

from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from transformations.common import (
    create_spark,
    read_clickhouse,
    read_latest_batch,
    write_clickhouse,
)

from etl.transformations.dimensions.scd.common import (
    add_hash,
    build_expired_version,
    build_new_version,
    split_changes,
)

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def transform_dim_farm(
    farm_df: DataFrame,
    infrastructure_type_df: DataFrame,
    growing_system_type_df: DataFrame,
) -> DataFrame:
    """
    Build the dim_farm SCD2 dimension from source tables.
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
        )
    )


def main():
    """
    Load the dim_farm warehouse dimension.
    """
    spark = create_spark("load_dim_farm")

    try:
        # Read the latest raw snapshots from the staging layer.
        farm_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "farms",
        )

        infrastructure_type_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "farm_infrastructure_types",
        )

        growing_system_type_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "growing_system_types",
        )

        # Build the warehouse dimension shape by enriching farms
        # with descriptive lookup values.
        dim_farm_df = transform_dim_farm(
            farm_df,
            infrastructure_type_df,
            growing_system_type_df,
        )

        # Read only the current SCD2 versions from ClickHouse.
        current_dim_farm_df = read_clickhouse(
            spark,
            """(SELECT * FROM dim_farm FINAL) AS dim_farm""",
        ).filter(col("is_current") == 1)

        # Hash business attributes to efficiently detect changes.
        source_hashed_df = add_hash(
            dim_farm_df,
            [
                "name",
                "city",
                "size_m2",
                "growing_beds_count",
                "status",
                "infrastructure_type_id",
                "infrastructure_type_name",
                "growing_system_type_id",
                "growing_system_type_name",
            ],
        )

        current_hashed_df = add_hash(
            current_dim_farm_df,
            [
                "name",
                "city",
                "size_m2",
                "growing_beds_count",
                "status",
                "infrastructure_type_id",
                "infrastructure_type_name",
                "growing_system_type_id",
                "growing_system_type_name",
            ],
        )

        # Compare source data with the current dimension state.
        new_farms_df, changed_farms_df = split_changes(
            source_hashed_df,
            current_hashed_df,
            "farm_id",
        )

        # Use a single version for all rows written during this load.
        load_version = int(time.time() * 1000)

        # New farms are inserted, while changed farms produce both
        # an expired version and a new current version.
        rows_to_write = (
            build_new_version(new_farms_df, load_version)
            .unionByName(
                build_expired_version(changed_farms_df, load_version, "farm_key")
            )
            .unionByName(build_new_version(changed_farms_df, load_version))
        )

        write_clickhouse(
            rows_to_write,
            "dim_farm",
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
