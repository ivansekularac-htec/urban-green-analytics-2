"""
Load fact_daily_farm_quality_metrics aggregate table.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    count,
    sum,
)
from transformations.common import (
    create_spark,
    read_clickhouse,
    write_clickhouse,
)
from transformations.facts.common import add_date_key


def build_daily_farm_quality_metrics(
    fact_harvests_df: DataFrame,
) -> DataFrame:
    """
    Aggregate harvest yield by farm, day, and quality grade.
    """

    return (
        fact_harvests_df.groupBy(
            "harvest_date",
            "farm_key",
            "farm_id",
            "quality_grade_id",
        )
        .agg(
            sum("weight_kg").alias(
                "total_yield_kg",
            ),
            count("*")
            .cast("integer")
            .alias(
                "harvest_count",
            ),
        )
        .withColumnRenamed(
            "harvest_date",
            "metric_date",
        )
    )


def transform_daily_farm_quality_metrics(
    fact_harvests_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:
    """
    Build daily farm quality metrics.
    """

    metrics_df = build_daily_farm_quality_metrics(
        fact_harvests_df,
    )

    metrics_df = add_date_key(
        metrics_df,
        dim_date_df,
        "metric_date",
    )

    return metrics_df


def main():
    spark = create_spark(
        "fact_daily_farm_quality_metrics",
    )

    try:
        fact_harvests_df = read_clickhouse(
            spark,
            "fact_harvests",
        )

        dim_date_df = read_clickhouse(
            spark,
            "dim_date",
        )

        daily_quality_metrics_df = transform_daily_farm_quality_metrics(
            fact_harvests_df,
            dim_date_df,
        )

        write_clickhouse(
            daily_quality_metrics_df,
            "fact_daily_farm_quality_metrics",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
