"""
Load fact_daily_sensor_metrics aggregate table.
"""

from pyspark.sql import DataFrame
from transformations.common import (
    create_spark,
    read_clickhouse,
    write_clickhouse,
)
from transformations.facts.common import (
    add_date_key,
    build_daily_sensor_metrics,
)


def transform_daily_sensor_metrics(
    fact_sensor_readings_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:
    """
    Build daily metrics per farm and sensor type.
    """

    metrics_df = build_daily_sensor_metrics(
        fact_sensor_readings_df,
    )

    metrics_df = add_date_key(
        metrics_df,
        dim_date_df,
        "metric_date",
    )

    return metrics_df.select(
        "metric_date",
        "date_key",
        "farm_key",
        "farm_id",
        "sensor_type_key",
        "reading_count",
        "sum_value",
        "min_value",
        "max_value",
        "anomaly_count",
        "in_range_count",
    )


def main():
    spark = create_spark(
        "fact_daily_sensor_metrics",
    )

    try:
        fact_sensor_readings_df = read_clickhouse(
            spark,
            "fact_sensor_readings",
        )

        dim_date_df = read_clickhouse(
            spark,
            "dim_date",
        )

        daily_sensor_metrics_df = transform_daily_sensor_metrics(
            fact_sensor_readings_df,
            dim_date_df,
        )

        write_clickhouse(
            daily_sensor_metrics_df,
            "fact_daily_sensor_metrics",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
