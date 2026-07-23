"""
Loads fact_farm_leaderboard into ClickHouse.

The job executes the leaderboard refresh pipeline:

1. Creates a Spark session.
2. Reads daily farm metrics.
3. Calculates farm rankings and composite scores.
4. Writes the leaderboard dataframe into ClickHouse.

The leaderboard is refreshed using the configured
aggregation refresh window.
"""

from aggregates.fact_farm_leaderboard import (
    create_fact_farm_leaderboard,
)
from common.clickhouse import write_to_clickhouse
from common.spark import get_spark_session


def main():
    """
    Runs the fact_farm_leaderboard loading job.

    The function creates the Spark session, generates the
    leaderboard dataframe, writes results into ClickHouse,
    and stops the Spark application.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-fact-farm-leaderboard",
    )

    try:
        fact_df = create_fact_farm_leaderboard(
            spark,
        )

        if not fact_df.rdd.isEmpty():
            write_to_clickhouse(
                fact_df,
                "fact_farm_leaderboard",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
