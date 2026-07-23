"""
Creates dim_role dimension from raw PostgreSQL parquet data.

The loader performs a full refresh on every run.
All available raw parquet files are read and the latest record
for each role is selected based on the ingestion batch timestamp.

The resulting dataframe represents the current state of the dimension
and is written to ClickHouse.
"""

from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql.functions import (
    col,
    current_timestamp,
)

ROLES_PATH = f"{RAW_POSTGRES_PATH}/roles/"


def create_dim_role(spark):
    """
    Creates the latest state of the dim_role dimension.

    The function reads all role records from raw parquet,
    keeps only the latest record for each role, and builds
    the dimension dataframe used for loading into ClickHouse.

    Returns
    -------
    DataFrame
        Dimension dataframe containing one latest row per role.
    """

    roles = read_latest_raw_parquet(
        spark,
        ROLES_PATH,
        "id",
    )

    dim_role_df = roles.select(
        col("id").cast("long").alias("role_id"),
        col("name"),
        col("description"),
        current_timestamp().alias("_loaded_at"),
    )

    return dim_role_df
