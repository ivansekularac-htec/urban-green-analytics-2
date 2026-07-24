from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import dag

SPARK_JOBS_DIR = "/opt/airflow/spark-jobs"

JARS_DIR = "/home/airflow/.local/lib/python3.10/site-packages/pyspark/jars"
JAR_FILES = (
    "clickhouse-jdbc-0.9.8-all-dependencies.jar",
    "hadoop-aws-3.4.1.jar",
    "bundle-2.29.52.jar",
)
JARS = ",".join(f"{JARS_DIR}/{jar}" for jar in JAR_FILES)

DRIVER_CONF = {
    "spark.driver.host": "urbangreen-airflow",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.memory": "512m",
    "spark.executor.memory": "1g",
    "spark.cores.max": "2",
    "spark.sql.session.timeZone": "UTC",
    "spark.sql.shuffle.partitions": "16",
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
}


def _submit(task_id: str, script: str) -> SparkSubmitOperator:
    return SparkSubmitOperator(
        task_id=task_id,
        conn_id="urbangreen_spark",
        deploy_mode="client",
        application=f"{SPARK_JOBS_DIR}/{script}",
        jars=JARS,
        verbose=True,
        conf=DRIVER_CONF,
    )


@dag(
    dag_id="warehouse_load",
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    tags=["warehouse", "spark", "clickhouse"],
)
def warehouse_load():
    # ------------------------------------------------------------------
    # Dimensions
    # ------------------------------------------------------------------

    load_dim_crop = _submit(
        "load_dim_crop",
        "dimensions/load_dim_crop.py",
    )

    load_dim_farm = _submit(
        "load_dim_farm",
        "dimensions/load_dim_farm.py",
    )

    load_dim_quality_grade = _submit(
        "load_dim_quality_grade",
        "dimensions/load_dim_quality_grade.py",
    )

    load_dim_role = _submit(
        "load_dim_role",
        "dimensions/load_dim_role.py",
    )

    load_dim_sensor_type = _submit(
        "load_dim_sensor_type",
        "dimensions/load_dim_sensor_type.py",
    )

    load_dim_sensor = _submit(
        "load_dim_sensor",
        "dimensions/load_dim_sensor.py",
    )

    load_dim_user = _submit(
        "load_dim_user",
        "dimensions/load_dim_user.py",
    )

    load_dim_user_farm_role = _submit(
        "load_dim_user_farm_role",
        "dimensions/load_dim_user_farm_role.py",
    )

    dims_done = EmptyOperator(task_id="dims_done")

    # ------------------------------------------------------------------
    # Facts
    # ------------------------------------------------------------------

    load_fact_harvests = _submit(
        "load_fact_harvests",
        "facts/load_fact_harvests.py",
    )

    load_fact_sensor_readings = _submit(
        "load_fact_sensor_readings",
        "facts/load_fact_sensor_readings.py",
    )

    facts_done = EmptyOperator(task_id="facts_done")

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    load_fact_daily_farm_metrics = _submit(
        "load_fact_daily_farm_metrics",
        "aggregates/load_fact_daily_farm_metrics.py",
    )

    load_fact_daily_farm_quality_metrics = _submit(
        "load_fact_daily_farm_quality_metrics",
        "aggregates/load_fact_daily_farm_quality_metrics.py",
    )

    load_fact_daily_sensor_metrics = _submit(
        "load_fact_daily_sensor_metrics",
        "aggregates/load_fact_daily_sensor_metrics.py",
    )

    aggs_done = EmptyOperator(task_id="aggs_done")

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    load_fact_farm_leaderboard = _submit(
        "load_fact_farm_leaderboard",
        "aggregates/load_fact_farm_leaderboard.py",
    )

    # ------------------------------------------------------------------
    # Dimension dependencies
    # ------------------------------------------------------------------

    load_dim_sensor_type >> load_dim_sensor

    [
        load_dim_user,
        load_dim_role,
        load_dim_farm,
    ] >> load_dim_user_farm_role

    [
        load_dim_crop,
        load_dim_quality_grade,
        load_dim_role,
        load_dim_user,
        load_dim_farm,
        load_dim_sensor_type,
        load_dim_sensor,
        load_dim_user_farm_role,
    ] >> dims_done

    # ------------------------------------------------------------------
    # Facts
    # ------------------------------------------------------------------

    dims_done >> [
        load_fact_harvests,
        load_fact_sensor_readings,
    ]

    [
        load_fact_harvests,
        load_fact_sensor_readings,
    ] >> facts_done

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    facts_done >> [
        load_fact_daily_farm_metrics,
        load_fact_daily_farm_quality_metrics,
        load_fact_daily_sensor_metrics,
    ]

    [
        load_fact_daily_farm_metrics,
        load_fact_daily_farm_quality_metrics,
        load_fact_daily_sensor_metrics,
    ] >> aggs_done

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    aggs_done >> load_fact_farm_leaderboard


warehouse_load()
