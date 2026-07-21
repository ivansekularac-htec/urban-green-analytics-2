"""
Read crop source data from MinIO, transform it, and load the dim_crop
warehouse table in ClickHouse.
"""

import os

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp, when
from transformations.common import create_spark, read_raw_table, write_clickhouse

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def transform_dim_quality_grade(quality_grade_df: DataFrame) -> DataFrame:
    """
    Build the dim_crop warehouse dimension by joining crops with their
    category metadata.
    """

    return quality_grade_df.select(
        quality_grade_df.id.alias("quality_grade_id"),
        quality_grade_df.code,
        quality_grade_df.name,
        quality_grade_df.description,
        when(quality_grade_df.code == "A", 1).otherwise(0).alias("is_premium"),
        current_timestamp().alias("_loaded_at"),
    )


def main():
    """
    Load the dim_crop dimension from raw PostgreSQL snapshots into ClickHouse.
    """
    spark = create_spark("load_dim_quality_grade")

    try:
        quality_grade_df = read_raw_table(
            spark,
            MINIO_STAGING_BUCKET,
            "quality_grades",
        )

        dim_quality_grade_df = transform_dim_quality_grade(quality_grade_df)

        # Write to ClickHouse. ReplacingMergeTree ensures repeated runs converge
        # to the latest version of each crop.
        write_clickhouse(
            dim_quality_grade_df,
            "dim_quality_grade",
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
