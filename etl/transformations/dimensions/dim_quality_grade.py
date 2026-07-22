"""
Read quality grade source data from MinIO, transform it, and load the
dim_quality_grade warehouse table in ClickHouse.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp, when
from transformations.common import (
    create_spark,
    read_current_snapshot,
    write_clickhouse,
)

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def transform_dim_quality_grade(quality_grade_df: DataFrame) -> DataFrame:
    """
    Build dim_quality_grade rows from quality grade source data.
    """

    return quality_grade_df.select(
        quality_grade_df.id.alias("quality_grade_id"),
        quality_grade_df.code,
        quality_grade_df.name,
        quality_grade_df.description,
        when(
            quality_grade_df.code == "A",
            1,
        )
        .otherwise(0)
        .alias("is_premium"),
        current_timestamp().alias("_loaded_at"),
    )


def main():
    """
    Load the dim_quality_grade dimension from raw PostgreSQL snapshots
    stored in MinIO into ClickHouse.
    """

    spark = create_spark("load_dim_quality_grade")

    try:
        quality_grade_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "quality_grades",
        )

        dim_quality_grade_df = transform_dim_quality_grade(
            quality_grade_df,
        )

        # Write transformed dimension data to ClickHouse.
        # ReplacingMergeTree resolves duplicate versions based on the table key.
        write_clickhouse(
            dim_quality_grade_df,
            "dim_quality_grade",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
