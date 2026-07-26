"""Hourly warehouse load: lake -> ClickHouse via SparkSubmitOperator."""

from __future__ import annotations

from datetime import datetime

from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import dag

JARS_DIR = "/home/airflow/.local/lib/python3.10/site-packages/pyspark/jars"
JAR_NAMES = (
    "clickhouse-jdbc-0.9.8-all-dependencies.jar",
    "hadoop-aws-3.4.1.jar",
    "bundle-2.29.52.jar",
)

JARS = ",".join(f"{JARS_DIR}/{jar}" for jar in JAR_NAMES)

DRIVER_CONF = {
    "spark.driver.host": "urbangreen-airflow",
    "spark.driver.bindAddress": "0.0.0.0",
    "spark.driver.memory": "1g",
    "spark.executor.memory": "1g",
    "spark.executor.cores": "1",
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
        application=f"/opt/airflow/spark-jobs/{script}",
        jars=JARS,
        verbose=True,
        conf=DRIVER_CONF,
    )


@dag(
    dag_id="warehouse_load",
    schedule="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["module-3", "warehouse", "spark", "clickhouse"],
)
def warehouse_load():
    dims = [
        _submit("load_dim_role", "dimensions/load_dim_role.py"),
        _submit("load_dim_quality_grade", "dimensions/load_dim_quality_grade.py"),
        _submit("load_dim_crop", "dimensions/load_dim_crop.py"),
        _submit("load_dim_user", "dimensions/load_dim_user.py"),
        _submit("load_dim_farm", "dimensions/load_dim_farm.py"),
        _submit("load_dim_sensor_type", "dimensions/load_dim_sensor_type.py"),
        _submit("load_dim_sensor", "dimensions/load_dim_sensor.py"),
        _submit("load_dim_user_farm_role", "dimensions/load_dim_user_farm_role.py"),
    ]
    dims_done = EmptyOperator(task_id="dims_done")

    facts = [
        _submit("load_fact_harvests", "facts/load_fact_harvests.py"),
        _submit("load_fact_sensor_readings", "facts/load_fact_sensor_readings.py"),
    ]
    facts_done = EmptyOperator(task_id="facts_done")

    aggs = [
        _submit(
            "load_fact_daily_farm_metrics",
            "aggregates/load_fact_daily_farm_metrics.py",
        ),
        _submit(
            "load_fact_daily_sensor_metrics",
            "aggregates/load_fact_daily_sensor_metrics.py",
        ),
        _submit(
            "load_fact_daily_farm_quality_metrics",
            "aggregates/load_fact_daily_farm_quality_metrics.py",
        ),
    ]
    aggs_done = EmptyOperator(task_id="aggs_done")

    leaderboard = _submit(
        "load_fact_farm_leaderboard",
        "aggregates/load_fact_farm_leaderboard.py",
    )

    dims >> dims_done >> facts >> facts_done >> aggs >> aggs_done >> leaderboard


warehouse_load()
