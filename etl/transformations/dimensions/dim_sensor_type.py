"""
Creates dim_sensor_type dimension from raw PostgreSQL parquet data.

The function reads sensor type definitions from raw PostgreSQL parquet
sources stored in MinIO and transforms them into the final dimension
structure.

The resulting dataframe represents the current snapshot of sensor types
and is used as input for SCD2 processing.
"""

from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql import DataFrame

SENSOR_TYPES_PATH = f"{RAW_POSTGRES_PATH}/sensor_types/"


def create_dim_sensor_type(
    spark,
) -> DataFrame:
    """
    Creates the current state of the dim_sensor_type dimension.

    The function reads the latest sensor type records from raw parquet
    data and selects the attributes required by the dimension table.

    The dataframe contains sensor type metadata such as name, unit,
    description, and optimal measurement ranges.

    Parameters
    ----------
    spark:
        Active SparkSession.

    Returns
    -------
    DataFrame
        Dimension dataframe containing the current sensor type state.
    """

    sensor_types = read_latest_raw_parquet(
        spark,
        SENSOR_TYPES_PATH,
        "id",
    )

    df = sensor_types.select(
        sensor_types.id.cast("long").alias("sensor_type_id"),
        sensor_types.name.alias("name"),
        sensor_types.unit.alias("unit"),
        sensor_types.description.alias("description"),
        sensor_types.optimal_min.cast("double").alias("optimal_min"),
        sensor_types.optimal_max.cast("double").alias("optimal_max"),
    )

    return df
