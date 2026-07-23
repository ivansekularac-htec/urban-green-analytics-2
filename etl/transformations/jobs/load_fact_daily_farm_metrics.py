"""
Executes the refresh loading of fact_daily_farm_metrics.

The job performs the following steps:

1. Creates a SparkSession.
2. Reads existing warehouse fact and dimension tables.
3. Calculates daily farm-level production and sensor metrics.
4. Writes the resulting dataframe into ClickHouse.

The refresh is based on the configured aggregation window,
allowing late arriving harvest and sensor data to update
recent metric dates.
"""

from aggregates.fact_daily_farm_metrics import (
    create_fact_daily_farm_metrics,
)
from common.clickhouse import write_to_clickhouse
from common.spark import get_spark_session


def main():
    """
    Runs the fact_daily_farm_metrics ETL pipeline.

    The function creates a Spark session, generates the
    aggregated fact dataframe, loads the result into ClickHouse,
    and stops the Spark application.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-fact-daily-farm-metrics",
    )

    try:
        fact_df = create_fact_daily_farm_metrics(
            spark,
        )

        if not fact_df.rdd.isEmpty():
            write_to_clickhouse(
                fact_df,
                "fact_daily_farm_metrics",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
