"""
Loads fact_harvests incrementally into ClickHouse.

The job executes the harvest ingestion pipeline:

1. Creates a Spark session.
2. Reads the previously stored cursor.
3. Extracts new or updated harvest records.
4. Writes transformed records into ClickHouse.
5. Updates the cursor state after successful loading.

The incremental state is tracked using the source updated_at timestamp.
"""

from common.clickhouse import write_to_clickhouse
from common.cursor import (
    get_cursor,
    save_cursor,
)
from common.spark import get_spark_session
from facts.fact_harvests import create_fact_harvest


def main():
    """
    Runs the fact_harvests loading job.

    The function creates the Spark session, executes incremental
    harvest loading, persists new records, updates cursor state,
    and stops the Spark application.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-fact-harvest",
    )

    job_name = "fact_harvest"

    try:
        cursor = get_cursor(
            spark,
            job_name,
        )

        fact_df, new_cursor = create_fact_harvest(
            spark,
            cursor,
        )

        if not fact_df.rdd.isEmpty():
            write_to_clickhouse(
                fact_df,
                "fact_harvests",
            )

            save_cursor(
                spark,
                job_name,
                {"updated_at": new_cursor["updated_at"]},
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
