"""
Load the dim_user_farm_role warehouse dimension.
"""

import os
import time

from pyspark.sql import DataFrame
from pyspark.sql.functions import coalesce, col, lit
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
        # Reconstruct current PostgreSQL state from all MinIO batches.
        user_role_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "user_roles",
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

        # Compare source state with active warehouse state.
        comparison_df = source_hashed_df.alias("source").join(
            current_hashed_df.alias(
                "current",
            ),
            "user_role_id",
            "left",
        )

        # New relationships.
        new_rows_df = comparison_df.filter(col("current.user_role_id").isNull()).select(
            "source.*",
        )

        # Existing relationships where attributes changed.
        changed_rows_df = comparison_df.filter(
            (col("current.user_role_id").isNotNull())
            & (col("source._hash") != col("current._hash"))
        )

        # Old versions to close.
        expired_rows_df = changed_rows_df.select(
            "current.*",
        )

        # New active versions.
        new_versions_df = changed_rows_df.select(
            "source.*",
        )

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
