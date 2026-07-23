"""
Load the dim_farm warehouse SCD2 dimension.
"""

import os
import time

from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from transformations.common import (
    create_spark,
    read_clickhouse,
    read_current_snapshot,
    write_clickhouse,
)
from transformations.dimensions.scd.common import (
    add_hash,
    build_expired_version,
    build_new_version,
    split_changes,
)

MINIO_STAGING_BUCKET = os.environ.get(
    "MINIO_STAGING_BUCKET",
    "staging",
)

# Initial SCD2 load: historical facts exist before the warehouse.
# Use beginning-of-time so facts can resolve the correct dimension version.
INITIAL_VALID_FROM = "1970-01-01 00:00:00"


def transform_dim_farm(
    farm_df: DataFrame,
    infrastructure_type_df: DataFrame,
    growing_system_type_df: DataFrame,
) -> DataFrame:
    """
    Build dim_farm warehouse shape from source snapshot
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
            infrastructure_type_df.name.alias(
                "infrastructure_type_name",
            ),
            farm_df.growing_system_type_id,
            growing_system_type_df.name.alias(
                "growing_system_type_name",
            ),
        )
    )


def main():
    """
    Load the dim_farm warehouse dimension as an SCD2 table.

    Source data is reconstructed from MinIO snapshots.
    SCD2 comparison determines which rows need new versions.
    """

    spark = create_spark("load_dim_farm")

    try:
        # Read the current state of all source tables.
        #
        # MinIO contains incremental batches, so this reconstructs the
        # latest PostgreSQL state by combining all batches and keeping
        # the newest record per primary key.
        farm_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "farms",
        )

        infrastructure_type_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "farm_infrastructure_types",
        )

        growing_system_type_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "growing_system_types",
        )

        # Build the complete current dimension state.
        dim_farm_source_df = transform_dim_farm(
            farm_df,
            infrastructure_type_df,
            growing_system_type_df,
        )

        # Read currently active SCD2 versions from ClickHouse.
        current_dim_farm_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_farm FINAL
                ) AS dim_farm
            """,
        ).filter(
            col("is_current") == 1,
        )

        # Add hashes to compare business attributes.
        #
        # The hash represents the state of the dimension row.
        # If the hash changes, a new SCD2 version is created.
        source_hashed_df = add_hash(
            dim_farm_source_df,
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

        # Detect new farms and changed farms.
        new_farms_df, changed_farms_df = split_changes(
            source_hashed_df,
            current_hashed_df,
            "farm_id",
        )

        # Find currently active versions that need to expire.
        expired_farms_df = current_dim_farm_df.join(
            changed_farms_df.select("farm_id"),
            "farm_id",
            "inner",
        )

        # Changed source rows become new active versions.
        new_versions_df = changed_farms_df

        # One version identifier for this warehouse load.
        load_version = int(
            time.time() * 1000,
        )

        is_initial_load = current_dim_farm_df.isEmpty()

        if is_initial_load:
            initial_valid_from = INITIAL_VALID_FROM
        else:
            initial_valid_from = None

        rows_to_write = (
            build_new_version(
                new_farms_df,
                load_version,
                ["farm_key"],
                valid_from=initial_valid_from,
            )
            .unionByName(
                build_expired_version(
                    expired_farms_df,
                    load_version,
                    ["farm_key"],
                )
            )
            .unionByName(
                build_new_version(
                    new_versions_df,
                    load_version,
                    ["farm_key"],
                    valid_from=None,
                )
            )
        )

        if rows_to_write.count() > 0:
            write_clickhouse(
                rows_to_write,
                "dim_farm",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
