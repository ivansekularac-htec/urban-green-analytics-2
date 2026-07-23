"""
Creates fact_sensor_readings from raw Kafka parquet data.

The transformation reads incremental sensor events from raw Kafka
parquet files, generates warehouse surrogate keys, and enriches
sensor readings with attributes from sensor, sensor type, date,
and time dimensions.

The transformation calculates anomaly flags by comparing sensor
values against configured optimal ranges from dim_sensor_type.

Incremental processing is controlled through cursor tracking based
on event timestamps, allowing only new sensor readings to be loaded.

Returns
-------
tuple
    DataFrame containing transformed sensor readings and the updated
    cursor value.
"""

from datetime import datetime

from common.clickhouse import read_clickhouse
from common.config import RAW_KAFKA_PATH
from common.raw import read_kafka_raw_parquet
from pyspark.sql.functions import (
    col,
    concat_ws,
    from_unixtime,
    hour,
    minute,
    to_date,
    when,
    xxhash64,
)
from pyspark.sql.functions import (
    max as spark_max,
)

SENSOR_READINGS_PATH = f"{RAW_KAFKA_PATH}/sensor_readings/"


def create_fact_sensor_readings(
    spark,
    cursor=None,
):
    """
    Creates incremental fact_sensor_readings dataframe.

    The function reads new sensor events, joins warehouse dimensions,
    creates reading surrogate keys, derives reading timestamps and
    dates, and calculates anomaly indicators.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session used for reading raw and warehouse data.

    cursor : dict, optional
        Previous ingestion cursor containing the latest processed event
        timestamp.

    Returns
    -------
    tuple
        A tuple containing:
        - transformed sensor readings DataFrame
        - dictionary with the new cursor value
    """

    readings = read_kafka_raw_parquet(
        spark,
        SENSOR_READINGS_PATH,
        cursor["event_date"] if cursor else None,
    )

    # if cursor:
    #     readings = readings.filter(col("event_date") > cursor["event_date"])
    if cursor:
        readings = readings.filter(col("timestamp") > cursor["timestamp"])

    sensors = (
        read_clickhouse(
            spark,
            "dim_sensor",
        )
        .filter(col("is_current") == 1)
        .select(
            "sensor_id",
            "sensor_key",
            "farm_key",
            "sensor_type_key",
        )
    )

    sensor_types = (
        read_clickhouse(
            spark,
            "dim_sensor_type",
        )
        .filter(col("is_current") == 1)
        .select(
            "sensor_type_id",
            "sensor_type_key",
            "optimal_min",
            "optimal_max",
        )
    )

    dates = read_clickhouse(
        spark,
        "dim_date",
    ).select(
        "date_key",
        "full_date",
    )

    times = read_clickhouse(
        spark,
        "dim_time",
    ).select(
        "time_key",
        "hour",
        "minute",
    )

    df = (
        readings.alias("r")
        .withColumn(
            "reading_key",
            xxhash64(
                concat_ws(
                    "|",
                    col("farm_sensor_id"),
                    col("timestamp"),
                )
            ).cast("long"),
        )
        .withColumn("reading_ts", from_unixtime(col("timestamp")).cast("timestamp"))
        .withColumn("reading_date", to_date(col("reading_ts")))
        .withColumn("reading_hour", hour(col("reading_ts")))
        .withColumn("reading_minute", minute(col("reading_ts")))
        .join(
            sensors.alias("s"),
            col("r.farm_sensor_id") == col("s.sensor_id"),
            "left",
        )
        .join(
            sensor_types.alias("st"),
            col("r.sensor_type_id") == col("st.sensor_type_id"),
            "left",
        )
        .join(
            dates.alias("d"),
            col("reading_date") == col("d.full_date"),
            "left",
        )
        .join(
            times.alias("t"),
            (col("reading_hour") == col("t.hour"))
            & (col("reading_minute") == col("t.minute")),
            "left",
        )
        .select(
            col("reading_key"),
            col("s.farm_key"),
            col("r.farm_id").cast("long").alias("farm_id"),
            col("s.sensor_key"),
            col("st.sensor_type_key"),
            col("d.date_key"),
            col("t.time_key"),
            col("reading_ts"),
            col("reading_date"),
            col("r.value").cast("double").alias("value"),
            when(
                (col("r.value") < col("st.optimal_min"))
                | (col("r.value") > col("st.optimal_max")),
                1,
            )
            .otherwise(0)
            .cast("int")
            .alias("is_anomaly"),
        )
    )

    cursor_row = readings.select(spark_max("timestamp").alias("timestamp")).collect()[0]

    new_cursor = {
        "timestamp": cursor_row["timestamp"],
        "event_date": str(datetime.fromtimestamp(cursor_row["timestamp"]).date()),
    }

    return df, new_cursor
