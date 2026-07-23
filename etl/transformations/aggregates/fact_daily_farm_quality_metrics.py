"""
Creates fact_daily_farm_quality_metrics from warehouse fact tables.

The aggregation calculates daily production metrics grouped by farm
and quality grade.

The source data comes from fact_harvests and is enriched with
current farm surrogate keys and date dimension attributes.

Only records inside the configured aggregation refresh window
are processed.
"""

from common.clickhouse import read_clickhouse
from common.config import AGG_REFRESH_DAYS
from pyspark.sql.functions import (
    col,
    count,
    current_date,
    date_sub,
)
from pyspark.sql.functions import (
    sum as spark_sum,
)


def create_fact_daily_farm_quality_metrics(spark):
    """
    Creates daily farm quality aggregation dataframe.

    The function:

    - reads harvest fact data
    - filters records inside the refresh window
    - aggregates yield and harvest count by farm and quality grade
    - enriches results with farm and date dimension keys

    Returns
    -------
    DataFrame
        Aggregated daily farm quality metrics ready for loading
        into fact_daily_farm_quality_metrics.
    """

    harvests = read_clickhouse(
        spark,
        "fact_harvests",
    )

    farms = (
        read_clickhouse(
            spark,
            "dim_farm",
        )
        .filter(col("is_current") == 1)
        .select(
            "farm_id",
            "farm_key",
        )
    )

    dates = read_clickhouse(
        spark,
        "dim_date",
    ).select(
        "date_key",
        "full_date",
    )

    harvests = harvests.filter(
        col("harvest_date")
        >= date_sub(
            current_date(),
            AGG_REFRESH_DAYS,
        )
    )

    metrics = harvests.groupBy(
        "farm_id",
        "date_key",
        "quality_grade_id",
    ).agg(
        spark_sum("weight_kg").alias("total_yield_kg"),
        count("*").alias("harvest_count"),
    )

    df = (
        metrics.join(
            farms,
            "farm_id",
            "left",
        )
        .join(
            dates,
            "date_key",
            "left",
        )
        .select(
            col("full_date").alias("metric_date"),
            "date_key",
            "farm_key",
            "farm_id",
            "quality_grade_id",
            col("total_yield_kg").cast("decimal(18,3)"),
            col("harvest_count").cast("int"),
        )
    )

    return df
