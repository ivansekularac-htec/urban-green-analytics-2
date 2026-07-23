from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    asc,
    col,
    dense_rank,
    desc,
    when,
)
from transformations.common import create_spark, read_clickhouse, write_clickhouse
from transformations.facts.common import (
    add_date_key,
    build_daily_harvest_metrics,
    build_daily_sensor_metrics,
)


def build_leaderboard(
    harvest_metrics_df: DataFrame,
    energy_metrics_df: DataFrame,
) -> DataFrame:
    """
    Combine daily harvest and energy metrics.
    """

    return (
        harvest_metrics_df.join(
            energy_metrics_df.select(
                "metric_date",
                "farm_key",
                "farm_id",
                "sum_value",
            ),
            [
                "metric_date",
                "farm_key",
                "farm_id",
            ],
            "left",
        )
        .withColumn(
            "energy_efficiency_kwh_per_kg",
            when(
                col("sum_value").isNull() | (col("total_yield_kg") == 0),
                None,
            ).otherwise(
                col("sum_value") / col("total_yield_kg"),
            ),
        )
        .drop("sum_value")
    )


def add_rankings(
    leaderboard_df: DataFrame,
) -> DataFrame:
    """
    Rank farms within each day.
    """

    window = Window.partitionBy(
        "metric_date",
    )

    leaderboard_df = (
        leaderboard_df.withColumn(
            "yield_rank",
            dense_rank().over(
                window.orderBy(
                    desc("total_yield_kg"),
                )
            ),
        )
        .withColumn(
            "quality_rank",
            dense_rank().over(
                window.orderBy(
                    desc("premium_yield_share"),
                )
            ),
        )
        .withColumn(
            "energy_rank",
            dense_rank().over(
                window.orderBy(
                    asc("energy_efficiency_kwh_per_kg"),
                )
            ),
        )
    )

    leaderboard_df = leaderboard_df.withColumn(
        "composite_score",
        col("yield_rank") + col("quality_rank") + col("energy_rank"),
    )

    return leaderboard_df.withColumn(
        "composite_rank",
        dense_rank().over(
            window.orderBy(
                "composite_score",
            )
        ),
    )


def transform_fact_farm_leaderboard(
    fact_harvests_df: DataFrame,
    fact_sensor_readings_df: DataFrame,
    dim_quality_grade_df: DataFrame,
    dim_sensor_type_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:

    harvest_metrics_df = build_daily_harvest_metrics(
        fact_harvests_df,
        dim_quality_grade_df,
    )

    harvest_metrics_df = harvest_metrics_df.withColumn(
        "premium_yield_share",
        col("premium_yield_kg") / col("total_yield_kg"),
    )

    energy_metrics_df = build_daily_sensor_metrics(
        fact_sensor_readings_df,
    )

    energy_metrics_df = energy_metrics_df.join(
        dim_sensor_type_df.select(
            "sensor_type_key",
            "sensor_type_id",
        ),
        "sensor_type_key",
    ).filter(col("sensor_type_id") == 5)

    leaderboard_df = build_leaderboard(
        harvest_metrics_df,
        energy_metrics_df,
    )

    leaderboard_df = leaderboard_df.withColumn(
        "premium_yield_share",
        col("premium_yield_kg") / col("total_yield_kg"),
    ).drop(
        "premium_yield_kg",
        "non_premium_yield_kg",
        "harvest_count",
    )

    leaderboard_df = add_date_key(
        leaderboard_df,
        dim_date_df,
        "metric_date",
    )

    leaderboard_df = add_rankings(
        leaderboard_df,
    )

    return leaderboard_df

    # .select(
    #     "metric_date",
    #     "date_key",
    #     "farm_key",
    #     "farm_id",
    #     "total_yield_kg",
    #     "premium_yield_share",
    #     "energy_efficiency_kwh_per_kg",
    #     "yield_rank",
    #     "quality_rank",
    #     "energy_rank",
    #     "composite_score",
    #     "composite_rank",
    # )


def main():

    spark = create_spark("fact_farm_leaderboard")

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

        leaderboard_df = transform_fact_farm_leaderboard(
            fact_harvests_df,
            fact_sensor_readings_df,
            dim_quality_grade_df,
            dim_sensor_type_df,
            dim_date_df,
        )

        write_clickhouse(
            leaderboard_df,
            "fact_farm_leaderboard",
            mode="overwrite",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
