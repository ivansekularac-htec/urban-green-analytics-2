"""Incrementally load sensor readings using a replay-safe Parquet file cursor."""

import logging
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

ETL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETL_ROOT))

from transformations.common.clickhouse import (
    execute_clickhouse_sql,
    read_clickhouse_table,
    table_name,
    write_clickhouse_table,
)
from transformations.common.config import Settings, load_settings
from transformations.common.lake_reader import read_kafka_topic
from transformations.common.load_state import commit_cursor, read_cursor
from transformations.common.spark_session import build_spark_session
from transformations.common.temporal_join import temporal_condition

JOB_NAME = "load_fact_sensor_readings"
SOURCE_TOPIC = "sensor_readings"
TARGET_TABLE = "fact_sensor_readings"


def read_new_file_slice(
    spark,
    settings: Settings,
    cursor: dict[str, Any],
) -> DataFrame:
    last_modified_ms = int(cursor.get("file_modified_at_ms", -1))
    processed_paths = {str(path) for path in cursor.get("file_paths", [])}

    source = read_kafka_topic(
        spark,
        settings,
        SOURCE_TOPIC,
    ).select(
        "*",
        F.col("_metadata.file_path").alias("_source_file"),
        F.unix_millis(F.col("_metadata.file_modification_time")).alias(
            "_file_modified_at_ms"
        ),
    )

    modified_at = F.col("_file_modified_at_ms")
    source_file = F.col("_source_file")

    condition = modified_at > last_modified_ms

    if processed_paths:
        condition = condition | (
            (modified_at == last_modified_ms)
            & ~source_file.isin(*sorted(processed_paths))
        )

    return source.filter(condition)


def build_next_cursor(
    dataframe: DataFrame,
    previous_cursor: dict[str, Any],
) -> dict[str, Any]:
    next_modified_ms = int(
        dataframe.agg(F.max("_file_modified_at_ms").alias("value")).first()["value"]
    )

    next_paths = {
        row["_source_file"]
        for row in (
            dataframe.filter(F.col("_file_modified_at_ms") == next_modified_ms)
            .select("_source_file")
            .distinct()
            .collect()
        )
    }

    previous_modified_ms = int(previous_cursor.get("file_modified_at_ms", -1))

    if next_modified_ms == previous_modified_ms:
        next_paths.update(str(path) for path in previous_cursor.get("file_paths", []))

    return {
        "file_modified_at_ms": next_modified_ms,
        "file_paths": sorted(next_paths),
    }


def transform_sensor_readings(
    readings: DataFrame,
    farms: DataFrame,
    sensors: DataFrame,
    sensor_types: DataFrame,
) -> DataFrame:
    reading_window = Window.partitionBy(
        "farm_sensor_id",
        "timestamp",
    ).orderBy(
        F.col("_file_modified_at_ms").desc(),
        F.col("_source_file").desc(),
    )

    readings = (
        readings.withColumn(
            "_row_number",
            F.row_number().over(reading_window),
        )
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
        .withColumn(
            "reading_ts",
            F.to_timestamp(F.from_unixtime(F.col("timestamp").cast("long"))),
        )
        .alias("r")
    )

    farms = farms.select(
        "farm_key",
        "farm_id",
        "valid_from",
        "valid_to",
    ).alias("f")

    sensors = sensors.select(
        "sensor_key",
        "sensor_id",
        "valid_from",
        "valid_to",
    ).alias("s")

    sensor_types = sensor_types.select(
        "sensor_type_key",
        "sensor_type_id",
        "optimal_min",
        "optimal_max",
        "valid_from",
        "valid_to",
    ).alias("st")

    joined = (
        readings.join(
            farms,
            temporal_condition(
                F.col("r.farm_id"),
                F.col("f.farm_id"),
                F.col("r.reading_ts"),
                F.col("f.valid_from"),
                F.col("f.valid_to"),
            ),
            "left",
        )
        .join(
            sensors,
            temporal_condition(
                F.col("r.farm_sensor_id"),
                F.col("s.sensor_id"),
                F.col("r.reading_ts"),
                F.col("s.valid_from"),
                F.col("s.valid_to"),
            ),
            "left",
        )
        .join(
            sensor_types,
            temporal_condition(
                F.col("r.sensor_type_id"),
                F.col("st.sensor_type_id"),
                F.col("r.reading_ts"),
                F.col("st.valid_from"),
                F.col("st.valid_to"),
            ),
            "left",
        )
    )

    reading_ts = F.col("r.reading_ts")
    value = F.col("r.value").cast("double")

    return joined.select(
        F.col("r.farm_sensor_id").cast("long").alias("farm_sensor_id"),
        F.col("r.timestamp").cast("long").alias("source_timestamp"),
        F.col("f.farm_key"),
        F.col("r.farm_id").cast("long").alias("farm_id"),
        F.col("s.sensor_key"),
        F.col("st.sensor_type_key"),
        F.date_format(reading_ts, "yyyyMMdd").cast("int").alias("date_key"),
        (F.hour(reading_ts) * 100 + F.minute(reading_ts)).cast("int").alias("time_key"),
        reading_ts.alias("reading_ts"),
        F.to_date(reading_ts).alias("reading_date"),
        value.alias("value"),
        F.when(
            (value < F.col("st.optimal_min")) | (value > F.col("st.optimal_max")),
            1,
        )
        .otherwise(0)
        .cast("byte")
        .alias("is_anomaly"),
    )


def validate_result(
    dataframe: DataFrame,
) -> None:
    has_invalid_rows = (
        dataframe.filter(
            F.col("farm_key").isNull()
            | F.col("sensor_key").isNull()
            | F.col("sensor_type_key").isNull()
        )
        .limit(1)
        .count()
        > 0
    )

    if has_invalid_rows:
        raise ValueError(
            "Some sensor readings do not match dim_farm, dim_sensor or dim_sensor_type"
        )


def write_sensor_readings(
    dataframe: DataFrame,
    settings: Settings,
) -> None:
    staging_table = f"{TARGET_TABLE}__staging_{uuid4().hex}"

    staging = table_name(settings, staging_table)
    target = table_name(settings, TARGET_TABLE)

    try:
        execute_clickhouse_sql(
            settings,
            f"""
            CREATE TABLE {staging} (
                farm_sensor_id UInt64,
                source_timestamp Int64,
                farm_key UInt64,
                farm_id UInt64,
                sensor_key UInt64,
                sensor_type_key UInt64,
                date_key UInt32,
                time_key UInt32,
                reading_ts DateTime64(3, 'UTC'),
                reading_date Date,
                value Float64,
                is_anomaly UInt8
            )
            ENGINE = MergeTree
            ORDER BY tuple()
            """,
        )

        write_clickhouse_table(
            dataframe,
            settings,
            staging_table,
        )

        execute_clickhouse_sql(
            settings,
            f"""
            INSERT INTO {target} (
                reading_key,
                farm_key,
                farm_id,
                sensor_key,
                sensor_type_key,
                date_key,
                time_key,
                reading_ts,
                reading_date,
                value,
                is_anomaly
            )
            SELECT
                cityHash64(
                    farm_sensor_id,
                    source_timestamp
                ),
                farm_key,
                farm_id,
                sensor_key,
                sensor_type_key,
                date_key,
                time_key,
                reading_ts,
                reading_date,
                value,
                is_anomaly
            FROM {staging}
            """,
        )

    finally:
        execute_clickhouse_sql(
            settings,
            f"DROP TABLE IF EXISTS {staging} SYNC",
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    spark = build_spark_session(JOB_NAME, settings)

    try:
        cursor = (
            read_cursor(
                spark,
                settings,
                JOB_NAME,
            )
            or {}
        )

        new_source = read_new_file_slice(
            spark,
            settings,
            cursor,
        ).cache()

        if new_source.isEmpty():
            logging.info("No new %s files", SOURCE_TOPIC)
            return

        next_cursor = build_next_cursor(
            new_source,
            cursor,
        )

        result = transform_sensor_readings(
            new_source,
            read_clickhouse_table(
                spark,
                settings,
                "dim_farm",
            ),
            read_clickhouse_table(
                spark,
                settings,
                "dim_sensor",
            ),
            read_clickhouse_table(
                spark,
                settings,
                "dim_sensor_type",
            ),
        ).cache()

        validate_result(result)

        write_sensor_readings(
            result,
            settings,
        )

        commit_cursor(
            settings,
            JOB_NAME,
            next_cursor,
        )

        logging.info(
            "Loaded %s; file cursor=%s",
            TARGET_TABLE,
            next_cursor["file_modified_at_ms"],
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
