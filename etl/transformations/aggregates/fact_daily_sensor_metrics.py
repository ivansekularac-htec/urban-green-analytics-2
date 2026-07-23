"""
Creates fact_daily_sensor_metrics from warehouse sensor data.

The aggregation calculates daily sensor statistics grouped by farm
and sensor type.

The source data comes from fact_sensor_readings and is enriched with
current farm surrogate keys and date dimension attributes.

Metrics include reading count, total value, minimum and maximum values,
and anomaly statistics.

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
    max as spark_max,
)
from pyspark.sql.functions import (
    min as spark_min,
)
from pyspark.sql.functions import (
    sum as spark_sum,
)


def create_fact_daily_sensor_metrics(spark):
    """
    Creates daily sensor metrics aggregation dataframe.

    The function:

    - reads sensor readings from fact_sensor_readings
    - filters data inside the aggregation refresh window
    - aggregates readings by farm, date, and sensor type
    - calculates sensor statistics and anomaly counts
    - enriches results with farm and date dimension keys

    Returns
    -------
    DataFrame
        Aggregated daily sensor metrics ready for loading
        into fact_daily_sensor_metrics.
    """

    readings = read_clickhouse(
        spark,
        "fact_sensor_readings",
    )

    dates = read_clickhouse(
        spark,
        "dim_date",
    ).select(
        "date_key",
        "full_date",
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

    readings = readings.filter(
        col("reading_date")
        >= date_sub(
            current_date(),
            AGG_REFRESH_DAYS,
        )
    )

    metrics = readings.groupBy(
        "farm_id",
        "date_key",
        "sensor_type_key",
    ).agg(
        count("*").alias("reading_count"),
        spark_sum("value").alias("sum_value"),
        spark_min("value").alias("min_value"),
        spark_max("value").alias("max_value"),
        spark_sum("is_anomaly").alias("anomaly_count"),
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
            "sensor_type_key",
            col("reading_count").cast("long"),
            col("sum_value").cast("double"),
            col("min_value").cast("double"),
            col("max_value").cast("double"),
            col("anomaly_count").cast("long"),
            (col("reading_count") - col("anomaly_count"))
            .cast("long")
            .alias("in_range_count"),
        )
    )

    return df
