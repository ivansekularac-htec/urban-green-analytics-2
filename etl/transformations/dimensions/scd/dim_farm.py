"""
Load the dim_farm warehouse dimension.
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
from transformations.dimensions.scd.common import (
    build_expired_version,
    build_new_version,
)

MINIO_STAGING_BUCKET = os.environ.get(
    "MINIO_STAGING_BUCKET",
    "staging",
)


def transform_dim_farm(
    farm_df: DataFrame,
    infrastructure_type_df: DataFrame,
    growing_system_type_df: DataFrame,
) -> DataFrame:
    """
    Build dim_farm rows from the latest farm changes.
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
    Load the dim_farm SCD2 dimension.
    """

    spark = create_spark("load_dim_farm")

    try:
        # Read changed source rows from the latest ingestion batch.
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

        # Enrich farms with descriptive lookup values.
        changed_farms_df = transform_dim_farm(
            farm_df,
            infrastructure_type_df,
            growing_system_type_df,
        )

        # Read current SCD2 versions.
        current_dim_farm_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_farm FINAL
                ) AS dim_farm
                """,
        ).filter(col("is_current") == 1)

        # Split incoming rows into:
        # - new farms (not yet in ClickHouse)
        # - existing farms (already have an active SCD2 version)
        new_farms_df = changed_farms_df.join(
            current_dim_farm_df.select("farm_id"),
            "farm_id",
            "left_anti",
        )

        updated_farms_df = changed_farms_df.join(
            current_dim_farm_df.select("farm_id"),
            "farm_id",
            "inner",
        )

        # Read the current versions that must be expired.
        current_versions_df = current_dim_farm_df.join(
            updated_farms_df.select("farm_id"),
            "farm_id",
            "inner",
        )

        # One version number for the whole load.
        load_version = int(time.time() * 1000)

        # Build rows to insert:
        # - new farms -> one active version
        # - updated farms -> expire old version + insert new version
        rows_to_write = (
            build_new_version(
                new_farms_df,
                load_version,
            )
            .unionByName(
                build_expired_version(
                    current_versions_df,
                    load_version,
                    "farm_key",
                )
            )
            .unionByName(
                build_new_version(
                    updated_farms_df,
                    load_version,
                )
            )
        )

        write_clickhouse(
            rows_to_write,
            "dim_farm",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
