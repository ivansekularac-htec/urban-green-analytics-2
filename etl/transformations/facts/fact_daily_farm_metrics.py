"""
Load fact_daily_farm_metrics aggregate table.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    max,
    sum,
)
from transformations.common import (
    create_spark,
    read_clickhouse,
    write_clickhouse,
)
from transformations.facts.common import (
    add_date_key,
    build_daily_harvest_metrics,
    build_daily_sensor_metrics,
)


def transform_daily_farm_metrics(
    fact_harvests_df: DataFrame,
    fact_sensor_readings_df: DataFrame,
    dim_quality_grade_df: DataFrame,
    dim_sensor_type_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:
    """
    Build daily farm-level metrics.

    Combines:
    - daily harvest metrics
    - daily energy consumption metrics
    - sensor quality metrics
    """

    # Harvest metrics per farm/day
    harvest_metrics_df = build_daily_harvest_metrics(
        fact_harvests_df,
        dim_quality_grade_df,
    )

    # Sensor metrics per farm/day/sensor type
    sensor_metrics_df = build_daily_sensor_metrics(
        fact_sensor_readings_df,
    )

    # Keep only energy sensors (sensor_type_id = 5)
    energy_metrics_df = sensor_metrics_df.join(
        dim_sensor_type_df.select(
            "sensor_type_key",
            "sensor_type_id",
        ),
        "sensor_type_key",
    ).filter(
        col("sensor_type_id") == 5,
    )

    # Aggregate energy metrics to farm/day level
    farm_sensor_metrics_df = energy_metrics_df.groupBy(
        "metric_date",
        "farm_key",
        "farm_id",
    ).agg(
        sum("sum_value").alias("energy_kwh"),
        sum("reading_count").alias("reading_count"),
        sum("anomaly_count").alias("anomaly_count"),
        sum("in_range_count").alias("in_range_count"),
        max("last_sensor_reading_ts").alias(
            "last_sensor_reading_ts",
        ),
    )

    # Combine harvest and sensor metrics
    metrics_df = harvest_metrics_df.join(
        farm_sensor_metrics_df,
        [
            "metric_date",
            "farm_key",
            "farm_id",
        ],
        "left",
    )

    # Add warehouse date attributes
    metrics_df = add_date_key(
        metrics_df,
        dim_date_df,
        "metric_date",
    )

    return metrics_df

    # .select(
    #     "metric_date",
    #     "date_key",
    #     "farm_key",
    #     "farm_id",
    #     "year_week",
    #     "total_yield_kg",
    #     "harvest_count",
    #     "premium_yield_kg",
    #     "non_premium_yield_kg",
    #     "energy_kwh",
    #     "reading_count",
    #     "anomaly_count",
    #     "in_range_count",
    #     "last_sensor_reading_ts",
    # )


def main():

    spark = create_spark(
        "fact_daily_farm_metrics",
    )

    try:
        fact_harvests_df = read_clickhouse(
            spark,
            "fact_harvests",
        )

        fact_sensor_readings_df = read_clickhouse(
            spark,
            "fact_sensor_readings",
        )

        dim_quality_grade_df = read_clickhouse(
            spark,
            "dim_quality_grade",
        )

        dim_sensor_type_df = read_clickhouse(
            spark,
            "dim_sensor_type",
        )

        dim_date_df = read_clickhouse(
            spark,
            "dim_date",
        )

        daily_metrics_df = transform_daily_farm_metrics(
            fact_harvests_df,
            fact_sensor_readings_df,
            dim_quality_grade_df,
            dim_sensor_type_df,
            dim_date_df,
        )

        write_clickhouse(
            daily_metrics_df,
            "fact_daily_farm_metrics",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
