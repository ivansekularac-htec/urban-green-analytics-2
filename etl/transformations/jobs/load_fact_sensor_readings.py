"""
Loads fact_sensor_readings incrementally into ClickHouse.

The job executes the sensor reading ingestion pipeline:

1. Creates a Spark session.
2. Reads the previously stored cursor.
3. Extracts new sensor events from raw Kafka parquet data.
4. Transforms and enriches readings with warehouse dimensions.
5. Writes transformed records into ClickHouse.
6. Updates the cursor state after successful loading.

The incremental state is tracked using the sensor event timestamp.
"""

from common.clickhouse import write_to_clickhouse
from common.cursor import (
    get_cursor,
    save_cursor,
)
from common.spark import get_spark_session
from facts.fact_sensor_readings import create_fact_sensor_readings


def main():
    """
    Executes the incremental fact_sensor_readings loading pipeline.

    The function creates a Spark session, retrieves the latest cursor
    state, generates new sensor reading records, writes them into
    ClickHouse, and saves the updated cursor after a successful load.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-fact-sensor-readings",
    )

    job_name = "fact_sensor_readings"

    try:
        cursor = get_cursor(
            spark,
            job_name,
        )

        fact_df, new_cursor = create_fact_sensor_readings(
            spark,
            cursor,
        )

        if not fact_df.rdd.isEmpty():
            write_to_clickhouse(
                fact_df,
                "fact_sensor_readings",
            )

            save_cursor(
                spark,
                job_name,
                {
                    "timestamp": new_cursor["timestamp"],
                    "event_date": new_cursor["event_date"],
                },
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
