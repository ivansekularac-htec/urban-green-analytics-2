"""
Loads fact_daily_farm_quality_metrics into ClickHouse.

The job executes the aggregation pipeline:

1. Creates a Spark session.
2. Builds daily farm quality metrics from fact_harvests.
3. Writes the resulting dataframe into ClickHouse.

The aggregation is refreshed using the configured
aggregation refresh window.
"""

from aggregates.fact_daily_farm_quality_metrics import (
    create_fact_daily_farm_quality_metrics,
)
from common.clickhouse import write_to_clickhouse
from common.spark import get_spark_session


def main():
    """
    Runs the fact_daily_farm_quality_metrics loading job.

    The function creates the Spark session, generates the
    aggregation dataframe, writes it to ClickHouse, and
    closes the Spark application.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-fact-daily-farm-quality-metrics",
    )

    try:
        fact_df = create_fact_daily_farm_quality_metrics(
            spark,
        )

        if not fact_df.rdd.isEmpty():
            write_to_clickhouse(
                fact_df,
                "fact_daily_farm_quality_metrics",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
