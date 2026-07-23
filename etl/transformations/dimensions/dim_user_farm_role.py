"""
Creates dim_user_farm_role dimension from raw PostgreSQL parquet data.

The function reads user-role assignments from raw PostgreSQL parquet
sources stored in MinIO and enriches them with user, role, and farm
descriptive attributes.

User and role information is loaded from ClickHouse dimensions,
while current farm records are taken from the SCD2 farm dimension.

The resulting dataframe represents the current snapshot of user
permissions and is used as input for SCD2 processing.
"""

from common.clickhouse import read_clickhouse
from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql import DataFrame
from pyspark.sql.functions import coalesce, col, lit

USER_ROLES_PATH = f"{RAW_POSTGRES_PATH}/user_roles/"


def create_dim_user_farm_role(
    spark,
) -> DataFrame:
    """
    Creates the current state of the dim_user_farm_role dimension.

    User-role assignments are enriched with descriptive information
    from user, role, and farm dimensions.

    Parameters
    ----------
    spark:
        Active SparkSession.

    Returns
    -------
    DataFrame
        Dimension dataframe containing user-role-farm assignments
        with descriptive attributes.
    """

    user_roles = read_latest_raw_parquet(
        spark,
        USER_ROLES_PATH,
        "id",
    )

    users = read_clickhouse(
        spark,
        "dim_user",
    )

    roles = read_clickhouse(
        spark,
        "dim_role",
    )

    farms = read_clickhouse(
        spark,
        "dim_farm",
    ).filter(col("is_current") == 1)

    df = (
        user_roles.alias("ur")
        .join(
            users.alias("u"),
            col("ur.user_id") == col("u.user_id"),
            "left",
        )
        .join(
            roles.alias("r"),
            col("ur.role_id") == col("r.role_id"),
            "left",
        )
        .join(
            farms.alias("f"),
            col("ur.farm_id") == col("f.farm_id"),
            "left",
        )
        .select(
            col("ur.id").cast("long").alias("user_role_id"),
            col("ur.user_id").cast("long").alias("user_id"),
            col("ur.role_id").cast("long").alias("role_id"),
            coalesce(col("ur.farm_id"), lit(0)).cast("long").alias("farm_id"),
            coalesce(col("f.farm_key"), lit(0)).cast("long").alias("farm_key"),
            col("u.full_name").alias("user_full_name"),
            col("r.name").alias("role_name"),
            coalesce(
                col("f.name"),
                lit(""),
            ).alias("farm_name"),
        )
    )

    return df
