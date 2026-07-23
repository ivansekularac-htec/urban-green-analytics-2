"""
Creates dim_farm dimension from raw PostgreSQL parquet data.

The function reads farm data together with related lookup tables
from raw parquet sources stored in MinIO.

Raw farm data is enriched with infrastructure and growing system
information to create the final dimension structure.

A change hash is generated from business attributes and used by
the SCD2 loader to detect changes between source and target records.

The function creates a complete current snapshot of the farm dimension.
"""

from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql import DataFrame

FARMS_PATH = f"{RAW_POSTGRES_PATH}/farms/"
FARM_INFRASTRUCTURE_TYPES_PATH = f"{RAW_POSTGRES_PATH}/farm_infrastructure_types/"
GROWING_SYSTEM_TYPES_PATH = f"{RAW_POSTGRES_PATH}/growing_system_types/"


def create_dim_farm(
    spark,
) -> DataFrame:
    """
    Creates the current state of the dim_farm dimension.

    The function reads raw farm data and enriches it with
    infrastructure and growing system lookup information.

    A change hash is added based on farm business attributes
    and is used during SCD2 comparison.

    Parameters
    ----------
    spark:
        Active SparkSession.

    Returns
    -------
    DataFrame
        Dimension dataframe containing the current farm state
        and change hash column used for SCD2 processing.
    """

    farms = read_latest_raw_parquet(
        spark,
        FARMS_PATH,
        "id",
    )

    infrastructure = read_latest_raw_parquet(
        spark,
        FARM_INFRASTRUCTURE_TYPES_PATH,
        "id",
    )

    growing_system = read_latest_raw_parquet(
        spark,
        GROWING_SYSTEM_TYPES_PATH,
        "id",
    )

    df = (
        farms.join(
            infrastructure,
            farms.infrastructure_type_id == infrastructure.id,
            "left",
        )
        .join(
            growing_system,
            farms.growing_system_type_id == growing_system.id,
            "left",
        )
        .select(
            farms.id.cast("long").alias("farm_id"),
            farms.name.alias("name"),
            farms.city.alias("city"),
            farms.size_m2.alias("size_m2"),
            farms.growing_beds_count.cast("int").alias("growing_beds_count"),
            farms.status.alias("status"),
            farms.infrastructure_type_id.cast("long").alias("infrastructure_type_id"),
            infrastructure.name.alias("infrastructure_type_name"),
            farms.growing_system_type_id.cast("long").alias("growing_system_type_id"),
            growing_system.name.alias("growing_system_type_name"),
        )
    )

    return df
