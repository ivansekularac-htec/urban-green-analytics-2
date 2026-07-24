"""Airflow DAG for the warehouse loading pipeline.

Runs the Spark ETL jobs every hour in four stages:
1. Load dimension tables.
2. Load fact tables.
3. Build aggregate tables.
4. Generate the farm leaderboard.

EmptyOperator barriers ensure that each stage completes before the next one
begins. Spark jobs are submitted in client mode through the configured Spark
connection.
"""

from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import dag

JARS_DIR = "/home/airflow/.local/lib/python3.10/site-packages/pyspark/jars"

JARS = ",".join(
    [
        f"{JARS_DIR}/clickhouse-jdbc-0.9.8-all-dependencies.jar",
        f"{JARS_DIR}/hadoop-aws-3.4.1.jar",
        f"{JARS_DIR}/bundle-2.29.52.jar",
    ]
)

DRIVER_CONF = {
    "spark.driver.host": "urbangreen-airflow",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.memory": "512m",
    "spark.executor.memory": "512m",
    "spark.cores.max": "1",
    "spark.sql.session.timeZone": "UTC",
}

# Spark jobs directories
SPARK_JOBS_DIR = "/opt/airflow/spark-jobs"

DIMENSIONS_DIR = "dimensions"
FACTS_DIR = "facts"
AGGREGATES_DIR = "aggregates"


def _submit(task_id: str, script: str, folder: str) -> SparkSubmitOperator:
    """Create a SparkSubmitOperator for a warehouse Spark job.

    Args:
        task_id: Airflow task identifier.
        script: Spark Python script filename.
        folder: Directory inside the Spark jobs mount.

    Returns:
        Configured SparkSubmitOperator.
    """

    return SparkSubmitOperator(
        task_id=task_id,
        conn_id="urbangreen_spark",
        deploy_mode="client",
        application=f"{SPARK_JOBS_DIR}/{folder}/{script}",
        jars=JARS,
        verbose=True,
        conf=DRIVER_CONF,
    )


@dag(
    dag_id="warehouse_load",
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    tags=["module-3", "warehouse", "spark", "clickhouse"],
)
def warehouse_load():
    """Run the hourly warehouse loading pipeline.

    The pipeline is organized into stages:
      1. Load dimension tables.
      2. Load fact tables.
      3. Build aggregated fact tables.
      4. Generate the farm leaderboard.

    EmptyOperator barriers ensure that each stage completes before the next
    stage begins.
    """

    # Dimension loads
    role = _submit(
        "load_dim_role",
        "load_dim_role.py",
        DIMENSIONS_DIR,
    )
    crop = _submit(
        "load_dim_crop",
        "load_dim_crop.py",
        DIMENSIONS_DIR,
    )
    user = _submit(
        "load_dim_user",
        "load_dim_user.py",
        DIMENSIONS_DIR,
    )
    quality_grade = _submit(
        "load_dim_quality_grade",
        "load_dim_quality_grade.py",
        DIMENSIONS_DIR,
    )
    farm = _submit(
        "load_dim_farm",
        "load_dim_farm.py",
        DIMENSIONS_DIR,
    )
    sensor_type = _submit(
        "load_dim_sensor_type",
        "load_dim_sensor_type.py",
        DIMENSIONS_DIR,
    )
    sensor = _submit(
        "load_dim_sensor",
        "load_dim_sensor.py",
        DIMENSIONS_DIR,
    )
    user_farm_role = _submit(
        "load_dim_user_farm_role",
        "load_dim_user_farm_role.py",
        DIMENSIONS_DIR,
    )
    dims_done = EmptyOperator(task_id="dims_done")

    # Fact loads
    facts = [
        _submit(
            "load_fact_harvest",
            "load_fact_harvests.py",
            FACTS_DIR,
        ),
        _submit(
            "load_fact_sensor_readings",
            "load_fact_sensor_readings.py",
            FACTS_DIR,
        ),
    ]

    facts_done = EmptyOperator(task_id="facts_done")

    # Aggregations
    aggs = [
        _submit(
            "load_fact_daily_farm_metrics",
            "load_fact_daily_farm_metrics.py",
            AGGREGATES_DIR,
        ),
        _submit(
            "load_fact_daily_sensor_metrics",
            "load_fact_daily_sensor_metrics.py",
            AGGREGATES_DIR,
        ),
        _submit(
            "load_fact_daily_farm_quality_metrics",
            "load_fact_daily_farm_quality_metrics.py",
            AGGREGATES_DIR,
        ),
    ]

    aggs_done = EmptyOperator(task_id="aggs_done")

    # Leaderboard
    leaderboard = _submit(
        "load_fact_farm_leaderboard",
        "load_fact_farm_leaderboard.py",
        AGGREGATES_DIR,
    )

    # Dependencies
    # user_farm_role enriches assignments with names from existing dimensions.
    [user, role, farm] >> user_farm_role

    # Wait for every dimension load before starting fact tables.
    [
        crop,
        quality_grade,
        sensor_type,
        sensor,
        user_farm_role,
    ] >> dims_done

    # Stage barriers.
    dims_done >> facts
    facts >> facts_done >> aggs
    aggs >> aggs_done >> leaderboard


warehouse_load()
