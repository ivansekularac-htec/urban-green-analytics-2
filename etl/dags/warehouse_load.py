"""
warehouse_load.py

Orchestrate the Spark jobs that populate the ClickHouse warehouse.

The DAG runs warehouse loaders in ordered stages:

1. Independent dimension loaders run in parallel.
2. The user-farm-role dimension runs after the user, role, and farm dimensions.
3. The dimensions barrier waits for all dimension loaders to finish.
4. Harvest and sensor-reading fact loaders run in parallel.
5. The facts barrier waits for both fact loaders to finish.
6. Daily aggregate loaders run in parallel.
7. The aggregates barrier waits for all aggregate loaders to finish.
8. The farm leaderboard loader runs last.

Each stage starts only after the preceding barrier completes successfully.
"""

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
    "spark.driver.memory": "512m",
    "spark.executor.memory": "512m",
    "spark.cores.max": "1",
    "spark.sql.session.timeZone": "UTC",
}

SPARK_JOBS_DIR = "/opt/airflow/spark-jobs"

DIMENSIONS_DIR = "dimensions"
FACTS_DIR = "facts"
AGGREGATES_DIR = "aggregates"


def _submit(task_id: str, script: str) -> SparkSubmitOperator:
    """Create a client-mode Spark submission for one warehouse loader."""
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
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    tags=["module-3", "warehouse", "spark", "clickhouse"],
)
def warehouse_load():
    """Run dimensions, facts, aggregates, and the leaderboard in order."""
    dimensions = {
        "crop": _submit(
            "load_dim_crop",
            f"{DIMENSIONS_DIR}/load_dim_crop.py",
        ),
        "farm": _submit(
            "load_dim_farm",
            f"{DIMENSIONS_DIR}/load_dim_farm.py",
        ),
        "quality_grade": _submit(
            "load_dim_quality_grade",
            f"{DIMENSIONS_DIR}/load_dim_quality_grade.py",
        ),
        "role": _submit(
            "load_dim_role",
            f"{DIMENSIONS_DIR}/load_dim_role.py",
        ),
        "sensor": _submit(
            "load_dim_sensor",
            f"{DIMENSIONS_DIR}/load_dim_sensor.py",
        ),
        "sensor_type": _submit(
            "load_dim_sensor_type",
            f"{DIMENSIONS_DIR}/load_dim_sensor_type.py",
        ),
        "user": _submit(
            "load_dim_user",
            f"{DIMENSIONS_DIR}/load_dim_user.py",
        ),
        "user_farm_role": _submit(
            "load_dim_user_farm_role",
            f"{DIMENSIONS_DIR}/load_dim_user_farm_role.py",
        ),
    }

    [
        dimensions["user"],
        dimensions["role"],
        dimensions["farm"],
    ] >> dimensions["user_farm_role"]

    dims_done = EmptyOperator(task_id="dims_done")
    list(dimensions.values()) >> dims_done

    facts = [
        _submit("load_fact_harvests", f"{FACTS_DIR}/load_fact_harvests.py"),
        _submit(
            "load_fact_sensor_readings",
            f"{FACTS_DIR}/load_fact_sensor_readings.py",
        ),
    ]

    facts_done = EmptyOperator(task_id="facts_done")
    dims_done >> facts
    facts >> facts_done

    aggregates = [
        _submit(
            "load_fact_daily_farm_metrics",
            f"{AGGREGATES_DIR}/load_fact_daily_farm_metrics.py",
        ),
        _submit(
            "load_fact_daily_farm_quality_metrics",
            f"{AGGREGATES_DIR}/load_fact_daily_farm_quality_metrics.py",
        ),
        _submit(
            "load_fact_daily_sensor_metrics",
            f"{AGGREGATES_DIR}/load_fact_daily_sensor_metrics.py",
        ),
    ]

    aggs_done = EmptyOperator(task_id="aggs_done")
    facts_done >> aggregates
    aggregates >> aggs_done

    leaderboard = _submit(
        "load_fact_farm_leaderboard",
        f"{AGGREGATES_DIR}/load_fact_farm_leaderboard.py",
    )

    aggs_done >> leaderboard


warehouse_load_dag = warehouse_load()
