"""
Load the dim_user_farm_role warehouse dimension.
"""

import os
import time

from pyspark.sql import DataFrame
from pyspark.sql.functions import coalesce, col, lit
from pyspark.sql.types import (
    LongType,
    StructField,
    StructType,
)
from transformations.common import (
    create_spark,
    read_clickhouse,
    read_current_snapshot,
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
    dim_farm_df: DataFrame,
) -> DataFrame:
    """
    Build the dim_user_farm_role source dataset.

    Uses dim_farm surrogate key because dim_farm is SCD2.
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
            dim_farm_df,
            user_role_df.farm_id == dim_farm_df.farm_id,
            "left",
        )
        .select(
            user_role_df.id.alias("user_role_id"),
            user_role_df.user_id,
            user_role_df.role_id,
            coalesce(
                dim_farm_df.farm_key,
                lit(0),
            ).alias("farm_key"),
            user_role_df.farm_id,
            user_df.full_name.alias("user_full_name"),
            role_df.name.alias("role_name"),
            dim_farm_df.name.alias("farm_name"),
        )
    )


def main():
    """
    Load dim_user_farm_role as an SCD2 dimension.
    """

    spark = create_spark("load_dim_user_farm_role")

    try:
        USER_ROLE_SCHEMA = StructType(
            [
                StructField("id", LongType(), True),
                StructField("user_id", LongType(), True),
                StructField("role_id", LongType(), True),
                StructField("farm_id", LongType(), True),
                StructField("created_at", LongType(), True),
                StructField("updated_at", LongType(), True),
            ]
        )

        # Read the current state of all source tables.
        #
        # MinIO contains incremental batches, so this reconstructs the
        # latest PostgreSQL state by combining all batches and keeping
        # the newest record per primary key.
        user_role_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "user_roles",
            schema=USER_ROLE_SCHEMA,
        )

        user_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "users",
        )

        role_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "roles",
        )

        # Read currently active SCD2 versions from ClickHouse.
        dim_farm_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_farm FINAL
                    WHERE is_current = 1
                ) AS dim_farm
            """,
        )

        # Build the complete current dimension state.
        dim_user_farm_role_source_df = transform_dim_user_farm_role(
            user_role_df,
            user_df,
            role_df,
            dim_farm_df,
        )

        # Read current active SCD2 versions.
        current_dim_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_user_farm_role FINAL
                ) AS dim_user_farm_role
            """,
        ).filter(
            col("is_current") == 1,
        )

        # Add hashes to compare business attributes.
        #
        # The hash represents the state of the dimension row.
        # If the hash changes, a new SCD2 version is created.
        hash_columns = [
            "user_id",
            "role_id",
            "farm_key",
            "farm_id",
            "user_full_name",
            "role_name",
            "farm_name",
        ]

        source_hashed_df = add_hash(
            dim_user_farm_role_source_df,
            hash_columns,
        )

        current_hashed_df = add_hash(
            current_dim_df,
            hash_columns,
        )

        # Detect new rows and changed rows.
        new_rows_df, changed_rows_df = split_changes(
            source_hashed_df,
            current_hashed_df,
            "user_role_id",
        )

        # Find currently active versions that need to expire.
        expired_rows_df = current_hashed_df.join(
            changed_rows_df.select("user_role_id"),
            "user_role_id",
            "inner",
        )

        # Changed source rows become new active versions.
        new_versions_df = changed_rows_df

        # One version identifier for this warehouse load.
        load_version = int(
            time.time() * 1000,
        )

        rows_to_write = (
            build_new_version(
                new_rows_df,
                load_version,
                [
                    "user_role_key",
                    "farm_key",
                ],
            )
            .unionByName(
                build_expired_version(
                    expired_rows_df,
                    load_version,
                    [
                        "user_role_key",
                        "farm_key",
                    ],
                )
            )
            .unionByName(
                build_new_version(
                    new_versions_df,
                    load_version,
                    [
                        "user_role_key",
                        "farm_key",
                    ],
                )
            )
        )

        if rows_to_write.count() > 0:
            write_clickhouse(
                rows_to_write,
                "dim_user_farm_role",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
