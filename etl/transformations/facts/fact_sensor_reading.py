"""
Load fact_sensor_readings incrementally into ClickHouse.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_date
from transformations.common import (
    create_spark,
    epoch_to_timestamp,
    read_clickhouse,
    read_incremental_parquet,
    write_clickhouse,
)
from transformations.facts.common import (
    add_date_key,
    add_farm_key,
    add_time_key,
)
from transformations.state import (
    get_watermark,
    set_watermark,
)

WATERMARK_PATH = "s3a://staging/_checkpoints/spark/fact_sensor_readings/watermark.json"

SOURCE_PATH = "s3a://staging/raw/kafka/sensor_readings/"


def transform_source(
    readings_df: DataFrame,
) -> DataFrame:
    """
    Normalize raw sensor readings for warehouse loading.
    """

    return readings_df.select(
        "farm_sensor_id",
        "farm_id",
        "sensor_type_id",
        "value",
        epoch_to_timestamp(
            readings_df.timestamp,
        ).alias("reading_ts"),
    ).withColumn(
        "reading_date",
        to_date("reading_ts"),
    )


def add_sensor_keys(
    readings_df: DataFrame,
    dim_sensor_df: DataFrame,
) -> DataFrame:
    """
    Resolve sensor surrogate keys from dim_sensor.

    Uses the sensor version active when the reading occurred.
    """

    return readings_df.join(
        dim_sensor_df,
        (
            (readings_df.farm_sensor_id == dim_sensor_df.sensor_id)
            & (readings_df.reading_ts >= dim_sensor_df.valid_from)
            & (readings_df.reading_ts < dim_sensor_df.valid_to)
        ),
        "left",
    ).select(
        readings_df["*"],
        dim_sensor_df.sensor_key,
        dim_sensor_df.sensor_type_key,
    )


def add_anomaly_flag(
    readings_df: DataFrame,
    dim_sensor_type_df: DataFrame,
) -> DataFrame:
    """
    Mark readings outside optimal sensor ranges.
    """

    return (
        readings_df.join(
            dim_sensor_type_df,
            (
                (readings_df.sensor_type_key == dim_sensor_type_df.sensor_type_key)
                & (readings_df.reading_ts >= dim_sensor_type_df.valid_from)
                & (readings_df.reading_ts < dim_sensor_type_df.valid_to)
            ),
            "left",
        )
        .withColumn(
            "is_anomaly",
            (
                (readings_df.value < dim_sensor_type_df.optimal_min)
                | (readings_df.value > dim_sensor_type_df.optimal_max)
            ).cast("integer"),
        )
        .select(
            readings_df["*"],
            "is_anomaly",
        )
    )


def transform_fact_sensor_readings(
    readings_df: DataFrame,
    dim_date_df: DataFrame,
    dim_farm_df: DataFrame,
    dim_sensor_df: DataFrame,
    dim_sensor_type_df: DataFrame,
) -> DataFrame:
    """
    Build fact_sensor_readings dataframe.
    """

    readings_df = transform_source(
        readings_df,
    )

    readings_df = add_date_key(
        readings_df,
        dim_date_df,
        "reading_date",
    )

    readings_df = add_time_key(
        readings_df,
        "reading_ts",
    )

    readings_df = add_farm_key(
        readings_df,
        dim_farm_df,
        "reading_ts",
    )

    readings_df = add_sensor_keys(
        readings_df,
        dim_sensor_df,
    )

    readings_df = add_anomaly_flag(
        readings_df,
        dim_sensor_type_df,
    )

    return readings_df.select(
        "farm_key",
        "farm_id",
        "sensor_key",
        "sensor_type_key",
        "date_key",
        "time_key",
        "reading_ts",
        "reading_date",
        "value",
        "is_anomaly",
    )


def main():

    spark = create_spark(
        "fact_sensor_readings",
    )

    try:
        last_watermark = get_watermark(
            spark,
            WATERMARK_PATH,
        )

        readings_df, newest_watermark = read_incremental_parquet(
            spark,
            SOURCE_PATH,
            last_watermark,
            watermark_parser=lambda value: value.split("=")[1],
            directory_prefix="event_date=",
        )

        if readings_df is None:
            print("No new sensor reading batches.")
            return

        dim_date_df = read_clickhouse(
            spark,
            "dim_date",
        )

        dim_farm_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_farm FINAL
                ) AS dim_farm
            """,
        )

        dim_sensor_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_sensor FINAL
                ) AS dim_sensor
            """,
        )

        dim_sensor_type_df = read_clickhouse(
            spark,
            """
                (
                    SELECT *
                    FROM dim_sensor_type FINAL
                ) AS dim_sensor_type
            """,
        )

        fact_df = transform_fact_sensor_readings(
            readings_df,
            dim_date_df,
            dim_farm_df,
            dim_sensor_df,
            dim_sensor_type_df,
        )

        if fact_df.filter(col("farm_key").isNull()).limit(1).count():
            raise RuntimeError("One or more farm keys could not be resolved.")

        if fact_df.filter(col("sensor_key").isNull()).limit(1).count():
            raise RuntimeError("One or more sensor keys could not be resolved.")

        if fact_df.filter(col("date_key").isNull()).limit(1).count():
            raise RuntimeError("One or more date keys could not be resolved.")

        write_clickhouse(
            fact_df,
            "fact_sensor_readings",
        )

        set_watermark(
            spark,
            WATERMARK_PATH,
            newest_watermark,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
