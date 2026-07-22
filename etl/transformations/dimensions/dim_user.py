"""
Read crop source data from MinIO, transform it, and load the dim_crop
warehouse table in ClickHouse.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp
from transformations.common import (
    create_spark,
    epoch_to_timestamp,
    read_current_snapshot,
    write_clickhouse,
)

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def transform_dim_user(user_df: DataFrame) -> DataFrame:
    """
    Build the dim_crop warehouse dimension by joining crops with their
    category metadata.
    """

    return user_df.select(
        user_df.id.alias("user_id"),
        user_df.email,
        user_df.full_name,
        user_df.is_active,
        epoch_to_timestamp(user_df.created_at).alias("created_at"),
        current_timestamp().alias("_loaded_at"),
    )


def main():
    """
    Load the dim_crop dimension from raw PostgreSQL snapshots into ClickHouse.
    """
    spark = create_spark("load_dim_user")

    try:
        user_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "users",
        )

        dim_user_df = transform_dim_user(user_df)

        # Write to ClickHouse. ReplacingMergeTree ensures repeated runs converge
        # to the latest version of each crop.
        write_clickhouse(
            dim_user_df,
            "dim_user",
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
