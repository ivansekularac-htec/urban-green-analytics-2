"""
Load the dim_user_farm_role warehouse dimension from raw snapshots.
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

MINIO_STAGING_BUCKET = os.environ.get(
    "MINIO_STAGING_BUCKET",
    "staging",
)


def transform_dim_user_farm_role(
    user_role_df: DataFrame,
    user_df: DataFrame,
    role_df: DataFrame,
    farm_df: DataFrame,
) -> DataFrame:
    """
    Build the dim_user_farm_role SCD2 dimension from source tables.
    """

    return (
        user_role_df.join(
            user_df,
            user_role_df.user_id == user_df.id,
            "left",
        )
        .join(
            role_df,
            user_role_df.role_id == role_df.id,
            "left",
        )
        .join(
            farm_df,
            user_role_df.farm_id == farm_df.id,
            "left",
        )
        .select(
            user_role_df.id.alias("user_role_id"),
            user_role_df.user_id,
            user_role_df.role_id,
            user_role_df.farm_id,
            user_df.full_name.alias("user_full_name"),
            role_df.name.alias("role_name"),
            farm_df.name.alias("farm_name"),
        )
    )


def main():
    """
    Load dim_user_farm_role from raw snapshots into ClickHouse.
    """

    spark = create_spark("load_dim_user_farm_role")

    try:
        # Read latest raw snapshots.
        user_role_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "user_roles",
        )

        user_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "users",
        )

        role_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "roles",
        )

        farm_df = read_latest_batch(
            spark,
            MINIO_STAGING_BUCKET,
            "farms",
        )

        # Build warehouse dimension shape.
        dim_user_farm_role_df = transform_dim_user_farm_role(
            user_role_df,
            user_df,
            role_df,
            farm_df,
        )

        # Read current SCD2 versions only.
        current_dim_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_user_farm_role FINAL
                ) AS dim_user_farm_role
                """,
        ).filter(col("is_current") == 1)

        # Detect changes using business attributes.
        source_hashed_df = add_hash(
            dim_user_farm_role_df,
            [
                "user_id",
                "role_id",
                "farm_id",
                "user_full_name",
                "role_name",
                "farm_name",
            ],
        )

        current_hashed_df = add_hash(
            current_dim_df,
            [
                "user_id",
                "role_id",
                "farm_id",
                "user_full_name",
                "role_name",
                "farm_name",
            ],
        )

        # Compare source snapshot with current warehouse state.
        new_rows_df, changed_rows_df = split_changes(
            source_hashed_df,
            current_hashed_df,
            "user_role_id",
        )

        load_version = int(time.time() * 1000)

        # Changed rows generate:
        # 1. expired old version
        # 2. new active version
        rows_to_write = (
            build_new_version(
                new_rows_df,
                load_version,
            )
            .unionByName(
                build_expired_version(
                    changed_rows_df,
                    load_version,
                    "user_role_key",
                )
            )
            .unionByName(
                build_new_version(
                    changed_rows_df,
                    load_version,
                )
            )
        )

        write_clickhouse(
            rows_to_write,
            "dim_user_farm_role",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
