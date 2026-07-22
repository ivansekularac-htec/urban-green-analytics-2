"""
Read crop source data from MinIO, transform it, and load the dim_crop
warehouse table in ClickHouse.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp
from transformations.common import (
    create_spark,
    read_current_snapshot,
    write_clickhouse,
)

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def transform_dim_role(roles_df: DataFrame) -> DataFrame:
    """
    Build the dim_crop warehouse dimension by joining crops with their
    category metadata.
    """

    return roles_df.select(
        roles_df.id.alias("role_id"),
        roles_df.name,
        roles_df.description,
        current_timestamp().alias("_loaded_at"),
    )


def main():
    """
    Load the dim_crop dimension from raw PostgreSQL snapshots into ClickHouse.
    """
    spark = create_spark("load_dim_role")

    try:
        roles_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "roles",
        )

        dim_role_df = transform_dim_role(roles_df)

        # Write to ClickHouse. ReplacingMergeTree ensures repeated runs converge
        # to the latest version of each crop.
        write_clickhouse(
            dim_role_df,
            "dim_role",
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
