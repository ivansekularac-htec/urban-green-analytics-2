"""Warehouse load DAG orchestrating Spark ETL jobs."""

from datetime import datetime, timezone

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
      "spark.driver.memory": "1g",
      "spark.executor.memory": "1g",
      "spark.cores.max": "2",
      "spark.sql.session.timeZone": "UTC",
      "spark.sql.shuffle.partitions": "16",
      "spark.sql.adaptive.enabled": "true",
      "spark.sql.adaptive.coalescePartitions.enabled": "true",
  }

DIMENSION_LOADERS = (
    ("load_dim_crop", "dimensions/load_dim_crop.py"),
    ("load_dim_farm", "dimensions/load_dim_farm.py"),
    ("load_dim_quality_grade", "dimensions/load_dim_quality_grade.py"),
    ("load_dim_role", "dimensions/load_dim_role.py"),
    ("load_dim_sensor", "dimensions/load_dim_sensor.py"),
    ("load_dim_sensor_type", "dimensions/load_dim_sensor_type.py"),
    ("load_dim_user", "dimensions/load_dim_user.py"),
    ("load_dim_user_farm_role", "dimensions/load_dim_user_farm_role.py"),
)
FACT_LOADERS = (
    ("load_fact_harvests", "facts/load_fact_harvests.py"),
    ("load_fact_sensor_readings", "facts/load_fact_sensor_readings.py"),
)
AGGREGATE_LOADERS = (
    (
        "load_fact_daily_farm_metrics",
        "aggregates/load_fact_daily_farm_metrics.py",
    ),
    (
        "load_fact_daily_farm_quality_metrics",
        "aggregates/load_fact_daily_farm_quality_metrics.py",
    ),
    (
        "load_fact_daily_sensor_metrics",
        "aggregates/load_fact_daily_sensor_metrics.py",
    ),
)


def _submit(task_id: str, script: str) -> SparkSubmitOperator:
    """Create a client-mode Spark submission for one warehouse loader."""
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
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    tags=["module-3", "warehouse", "spark", "clickhouse"],
)
def warehouse_load():
    """Run dimensions, facts, aggregates, and the leaderboard in order."""
    dimensions = {
        task_id: _submit(task_id, script)
        for task_id, script in DIMENSION_LOADERS
    }

    [
        dimensions["load_dim_user"],
        dimensions["load_dim_role"],
        dimensions["load_dim_farm"],
    ] >> dimensions["load_dim_user_farm_role"]

    dims_done = EmptyOperator(task_id="dims_done")
    list(dimensions.values()) >> dims_done

    facts = [_submit(task_id, script) for task_id, script in FACT_LOADERS]

    facts_done = EmptyOperator(task_id="facts_done")
    dims_done >> facts
    facts >> facts_done

    aggregates = [
        _submit(task_id, script)
        for task_id, script in AGGREGATE_LOADERS
    ]

    aggs_done = EmptyOperator(task_id="aggs_done")
    facts_done >> aggregates
    aggregates >> aggs_done

    leaderboard = _submit(
        "load_fact_farm_leaderboard",
        "aggregates/load_fact_farm_leaderboard.py",
    )
    aggs_done >> leaderboard


warehouse_load_dag = warehouse_load()
