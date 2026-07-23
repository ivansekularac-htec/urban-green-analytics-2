"""
Loads fact_daily_sensor_metrics into ClickHouse.

The job executes the daily sensor aggregation pipeline:

1. Creates a Spark session.
2. Generates sensor metrics from fact_sensor_readings.
3. Writes the resulting dataframe into ClickHouse.

The aggregation is refreshed using the configured
aggregation refresh window.
"""

from aggregates.fact_daily_sensor_metrics import (
    create_fact_daily_sensor_metrics,
)
from common.clickhouse import write_to_clickhouse
from common.spark import get_spark_session


def main():
    """
    Runs the fact_daily_sensor_metrics loading job.

    The function creates the Spark session, builds the aggregation
    dataframe, writes the results into ClickHouse, and stops
    the Spark application.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-fact-daily-sensor-metrics",
    )

    try:
        fact_df = create_fact_daily_sensor_metrics(
            spark,
        )

        if not fact_df.rdd.isEmpty():
            write_to_clickhouse(
                fact_df,
                "fact_daily_sensor_metrics",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
