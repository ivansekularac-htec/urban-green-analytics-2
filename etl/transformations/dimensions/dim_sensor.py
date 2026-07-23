"""
Creates dim_sensor dimension from raw PostgreSQL parquet data.

The function reads sensor records from raw PostgreSQL parquet
sources stored in MinIO and enriches them with surrogate keys
from current farm and sensor type dimensions.

Farm and sensor type information is loaded from existing SCD2
dimensions, using only current active records.

The resulting dataframe represents the current snapshot of sensors
and is used as input for SCD2 processing.
"""

from common.clickhouse import read_clickhouse
from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql import DataFrame
from pyspark.sql.functions import col

SENSORS_PATH = f"{RAW_POSTGRES_PATH}/sensors/"


def create_dim_sensor(
    spark,
) -> DataFrame:
    """
    Creates the current state of the dim_sensor dimension.

    The function reads the latest sensor records from raw parquet
    data and enriches them with current farm and sensor type
    dimension keys.

    Parameters
    ----------
    spark:
        Active SparkSession.

    Returns
    -------
    DataFrame
        Dimension dataframe containing the current sensor state.
    """

    sensors = read_latest_raw_parquet(
        spark,
        SENSORS_PATH,
        "id",
    )

    farms = read_clickhouse(
        spark,
        "dim_farm",
    ).filter(col("is_current") == 1)

    sensor_types = read_clickhouse(
        spark,
        "dim_sensor_type",
    ).filter(col("is_current") == 1)

    df = (
        sensors.alias("s")
        .join(
            farms.alias("f"),
            col("s.farm_id") == col("f.farm_id"),
            "left",
        )
        .join(
            sensor_types.alias("st"),
            col("s.sensor_type_id") == col("st.sensor_type_id"),
            "left",
        )
        .select(
            col("s.id").cast("long").alias("sensor_id"),
            col("f.farm_key").alias("farm_key"),
            col("st.sensor_type_key").alias("sensor_type_key"),
            col("s.serial_number").alias("serial_number"),
            col("s.status").alias("status"),
            col("s.installed_at").cast("timestamp").alias("installed_at"),
        )
    )

    return df
