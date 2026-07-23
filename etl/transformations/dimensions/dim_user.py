"""
Creates dim_user dimension from raw PostgreSQL parquet data.

The loader performs a full refresh on every run.
All available raw parquet files are read and the latest record
for each user is selected based on the ingestion batch timestamp.

The resulting dataframe represents the current state of the dimension
and is written to ClickHouse.
"""

from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql.functions import (
    col,
    current_timestamp,
    from_unixtime,
)

USERS_PATH = f"{RAW_POSTGRES_PATH}/users/"


def create_dim_user(spark):
    """
    Creates the latest state of the dim_user dimension.

    The function reads all user records from raw parquet,
    keeps only the latest record for each user, and builds
    the dimension dataframe used for loading into ClickHouse.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.

    Returns
    -------
    DataFrame
        Dimension dataframe containing one latest row per user.
    """

    users = read_latest_raw_parquet(
        spark,
        USERS_PATH,
        "id",
    )

    dim_user_df = users.select(
        col("id").cast("long").alias("user_id"),
        col("email"),
        col("full_name"),
        col("is_active").cast("integer").alias("is_active"),
        from_unixtime(col("created_at")).cast("timestamp").alias("created_at"),
        current_timestamp().alias("_loaded_at"),
    )

    return dim_user_df
