"""
Creates fact_daily_farm_metrics fact table.

The transformation aggregates daily farm performance metrics
from existing warehouse fact tables.

The function combines:
- harvest production data from fact_harvests
- sensor measurements from fact_sensor_readings
- quality information from dim_quality_grade
- sensor metadata from dim_sensor_type
- farm and date surrogate keys from dimensions

Calculated metrics include:
- total yield
- harvest count
- premium and non-premium yield
- energy consumption
- sensor reading count
- anomaly count
- in-range reading count
- latest sensor reading timestamp

Only data inside the configured aggregation refresh window
is processed to allow late arriving data corrections.
"""

from common.clickhouse import read_clickhouse
from common.config import AGG_REFRESH_DAYS
from pyspark.sql.functions import (
    coalesce,
    col,
    count,
    current_date,
    date_sub,
    lit,
    when,
)
from pyspark.sql.functions import (
    max as spark_max,
)
from pyspark.sql.functions import (
    sum as spark_sum,
)


def create_fact_daily_farm_metrics(spark):
    """
    Creates daily farm metrics dataframe.

    The function reads existing warehouse tables,
    applies aggregations by farm and date, enriches the
    result with dimension keys, and returns the dataframe
    ready for loading into ClickHouse.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session used for reading warehouse tables.

    Returns
    -------
    DataFrame
        Aggregated daily farm metrics dataframe.
    """

    harvests = read_clickhouse(
        spark,
        "fact_harvests",
    )

    readings = read_clickhouse(
        spark,
        "fact_sensor_readings",
    )

    quality = read_clickhouse(
        spark,
        "dim_quality_grade",
    ).select(
        "quality_grade_id",
        "is_premium",
    )

    sensor_types = read_clickhouse(
        spark,
        "dim_sensor_type",
    ).select(
        "sensor_type_key",
        "name",
    )

    dates = read_clickhouse(
        spark,
        "dim_date",
    ).select(
        "date_key",
        "full_date",
        "year_week",
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

    harvests = harvests.filter(
        col("harvest_date")
        >= date_sub(
            current_date(),
            AGG_REFRESH_DAYS,
        )
    )

    readings = readings.filter(
        col("reading_date")
        >= date_sub(
            current_date(),
            AGG_REFRESH_DAYS,
        )
    )

    harvest_metrics = (
        harvests.alias("h")
        .join(
            quality.alias("q"),
            col("h.quality_grade_id") == col("q.quality_grade_id"),
            "left",
        )
        .groupBy(
            "h.farm_id",
            "h.date_key",
        )
        .agg(
            spark_sum("h.weight_kg").alias("total_yield_kg"),
            count("*").alias("harvest_count"),
            spark_sum(
                when(
                    col("q.is_premium") == 1,
                    col("h.weight_kg"),
                ).otherwise(0)
            ).alias("premium_yield_kg"),
        )
    )

    sensor_metrics = (
        readings.alias("r")
        .join(
            sensor_types.alias("st"),
            col("r.sensor_type_key") == col("st.sensor_type_key"),
            "left",
        )
        .groupBy(
            "r.farm_id",
            "r.date_key",
        )
        .agg(
            spark_sum(
                when(
                    col("st.name") == "Energy Usage",
                    col("r.value"),
                ).otherwise(0)
            ).alias("energy_kwh"),
            count("*").alias("reading_count"),
            spark_sum("r.is_anomaly").alias("anomaly_count"),
            spark_max("r.reading_ts").alias("last_sensor_reading_ts"),
        )
    )

    df = (
        harvest_metrics.join(
            sensor_metrics,
            [
                "farm_id",
                "date_key",
            ],
            "full",
        )
        .join(
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
            "year_week",
            coalesce(
                col("total_yield_kg"),
                lit(0),
            ).alias("total_yield_kg"),
            coalesce(
                col("harvest_count"),
                lit(0),
            ).alias("harvest_count"),
            coalesce(
                col("premium_yield_kg"),
                lit(0),
            ).alias("premium_yield_kg"),
            (
                coalesce(
                    col("total_yield_kg"),
                    lit(0),
                )
                - coalesce(
                    col("premium_yield_kg"),
                    lit(0),
                )
            ).alias("non_premium_yield_kg"),
            coalesce(
                col("energy_kwh"),
                lit(0),
            ).alias("energy_kwh"),
            coalesce(
                col("reading_count"),
                lit(0),
            ).alias("reading_count"),
            coalesce(
                col("anomaly_count"),
                lit(0),
            ).alias("anomaly_count"),
            (
                coalesce(
                    col("reading_count"),
                    lit(0),
                )
                - coalesce(
                    col("anomaly_count"),
                    lit(0),
                )
            ).alias("in_range_count"),
            "last_sensor_reading_ts",
        )
    )

    return df
