from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, hour, lit, max, min, minute, sum, when


def add_farm_key(
    df: DataFrame,
    dim_farm_df: DataFrame,
    timestamp_column: str,
) -> DataFrame:
    """
    Add farm_key by resolving the SCD2 farm version
    active at the event timestamp.

    A farm_id can have multiple versions in dim_farm,
    therefore the join must include the valid_from / valid_to range.
    """

    return df.join(
        dim_farm_df,
        (
            (df.farm_id == dim_farm_df.farm_id)
            & (df[timestamp_column] >= dim_farm_df.valid_from)
            & (df[timestamp_column] < dim_farm_df.valid_to)
        ),
        "left",
    ).select(
        df["*"],
        dim_farm_df.farm_key,
    )


def add_date_key(
    df: DataFrame,
    dim_date_df: DataFrame,
    date_column: str,
) -> DataFrame:
    """
    Add date_key from dim_date.

    date_column:
        Name of the date column in the dataframe
        that should match dim_date.full_date.
    """

    return df.join(
        dim_date_df,
        df[date_column] == dim_date_df.full_date,
        "left",
    ).select(
        df["*"],
        dim_date_df.date_key,
    )


def add_time_key(
    df: DataFrame,
    timestamp_column: str,
) -> DataFrame:
    """
    Add minute-grain time_key.

    time_key format:
        hour * 100 + minute

    Examples:
        08:15 -> 815
        14:30 -> 1430
    """

    return df.withColumn(
        "time_key",
        hour(df[timestamp_column]) * 100 + minute(df[timestamp_column]),
    )


def build_daily_harvest_metrics(
    fact_harvests_df: DataFrame,
    dim_quality_grade_df: DataFrame,
) -> DataFrame:
    """
    Build daily harvest metrics for each farm.
    """

    return (
        fact_harvests_df.join(
            dim_quality_grade_df.select(
                "quality_grade_id",
                "is_premium",
            ),
            "quality_grade_id",
        )
        .groupBy(
            "harvest_date",
            "farm_key",
            "farm_id",
        )
        .agg(
            sum("weight_kg").alias("total_yield_kg"),
            sum(
                when(
                    col("is_premium") == 1,
                    col("weight_kg"),
                ).otherwise(
                    lit(0),
                )
            ).alias("premium_yield_kg"),
            sum(
                when(
                    col("is_premium") == 0,
                    col("weight_kg"),
                ).otherwise(
                    lit(0),
                )
            ).alias("non_premium_yield_kg"),
            count("*").cast("integer").alias("harvest_count"),
        )
        .withColumnRenamed(
            "harvest_date",
            "metric_date",
        )
    )


def build_daily_sensor_metrics(
    fact_sensor_readings_df: DataFrame,
) -> DataFrame:
    """
    Build daily sensor metrics for each farm and sensor type.
    """

    return (
        fact_sensor_readings_df.groupBy(
            "reading_date",
            "farm_key",
            "farm_id",
            "sensor_type_key",
        )
        .agg(
            count("*").cast("long").alias("reading_count"),
            sum("value").alias("sum_value"),
            min("value").alias("min_value"),
            max("value").alias("max_value"),
            sum(
                when(
                    col("is_anomaly") == 1,
                    1,
                ).otherwise(
                    0,
                )
            ).alias("anomaly_count"),
            sum(
                when(
                    col("is_anomaly") == 0,
                    1,
                ).otherwise(
                    0,
                )
            ).alias("in_range_count"),
            max("reading_ts").alias("last_sensor_reading_ts"),
        )
        .withColumnRenamed(
            "reading_date",
            "metric_date",
        )
    )
