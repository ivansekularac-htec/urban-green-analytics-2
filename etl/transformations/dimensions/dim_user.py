"""
Read user source data from MinIO, transform it, and load the dim_user
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
    Build dim_user rows from user source data.
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
    Load the dim_user dimension from raw PostgreSQL snapshots
    stored in MinIO into ClickHouse.
    """

    spark = create_spark("load_dim_user")

    try:
        user_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "users",
        )

        dim_user_df = transform_dim_user(user_df)

        # Write transformed dimension data to ClickHouse.
        # ReplacingMergeTree resolves duplicate versions based on the table key.
        write_clickhouse(
            dim_user_df,
            "dim_user",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
