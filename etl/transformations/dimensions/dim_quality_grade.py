"""
Creates dim_quality_grade dimension from raw PostgreSQL parquet data.

The loader performs a full refresh on every run.
All available raw parquet files are read and the latest record
for each quality grade is selected based on the ingestion batch
timestamp.

The resulting dataframe represents the current state of the dimension
and is written to ClickHouse.
"""

from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql.functions import (
    col,
    current_timestamp,
    when,
)

QUALITY_GRADES_PATH = f"{RAW_POSTGRES_PATH}/quality_grades/"


def create_dim_quality_grade(spark):
    """
    Creates the latest state of the dim_quality_grade dimension.

    The function reads all quality grade records from raw parquet,
    keeps only the latest record for each quality grade, and builds
    the dimension dataframe used for loading into ClickHouse.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.

    Returns
    -------
    DataFrame
        Dimension dataframe containing one latest row per quality grade.
    """

    quality_grades = read_latest_raw_parquet(
        spark,
        QUALITY_GRADES_PATH,
        "id",
    )

    dim_quality_grade_df = quality_grades.select(
        col("id").cast("long").alias("quality_grade_id"),
        col("code"),
        col("name"),
        col("description"),
        when(
            col("code") == "A",
            1,
        )
        .otherwise(0)
        .cast("integer")
        .alias("is_premium"),
        current_timestamp().alias("_loaded_at"),
    )

    return dim_quality_grade_df
