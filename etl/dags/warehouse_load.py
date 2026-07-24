"""warehouse_load - orchestrates the ClickHouse warehouse loaders hourly.

Each loader is a standalone spark-submit job. The DAG runs them in phases -
dimensions, then facts, then daily aggregates, then the leaderboard - with an
EmptyOperator barrier between phases so a phase starts only after the previous
one has fully finished.

Fully serialized on purpose: spark.cores.max = 1 gives each driver a single
core, so this batch load and the always-on streaming job share the two-core
cluster without starving one another. max_active_runs = 1 keeps two warehouse
runs from overlapping.

deploy_mode is client, so the driver runs inside the airflow container; the
executors reach it back over the compose network, which is why the driver host
and bind address are pinned in the conf.
"""

from __future__ import annotations

from datetime import datetime

from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import dag

# Spark ships its own jars inside the airflow image; the loaders need the
# ClickHouse JDBC driver and the S3A stack to reach ClickHouse and MinIO.
JARS_DIR = "/home/airflow/.local/lib/python3.10/site-packages/pyspark/jars"
JARS = ",".join(
    f"{JARS_DIR}/{jar}"
    for jar in (
        "clickhouse-jdbc-0.9.8-all-dependencies.jar",
        "hadoop-aws-3.4.1.jar",
        "bundle-2.29.52.jar",
    )
)

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

# Loader scripts, relative to the /opt/airflow/spark-jobs mount.

# Independent dimensions: each reads only its own raw source, so they load in
# parallel within the phase.
DIMENSIONS = [
    "dimensions/load_dim_role.py",
    "dimensions/load_dim_quality_grade.py",
    "dimensions/load_dim_crop.py",
    "dimensions/load_dim_user.py",
    "dimensions/load_dim_sensor_type.py",
    "dimensions/load_dim_farm.py",
    "dimensions/load_dim_sensor.py",
]

# Not independent: load_dim_user_farm_role denormalizes user / role / farm names
# by reading dim_user, dim_role and dim_farm from the warehouse, so it runs
# after those three rather than beside them.
USER_FARM_ROLE = "dimensions/load_dim_user_farm_role.py"
USER_FARM_ROLE_PARENTS = ("load_dim_user", "load_dim_role", "load_dim_farm")

FACTS = [
    "facts/load_fact_harvests.py",
    "facts/load_fact_sensor_readings.py",
]

AGGREGATES = [
    "aggregates/load_fact_daily_farm_quality_metrics.py",
    "aggregates/load_fact_daily_sensor_metrics.py",
    "aggregates/load_fact_daily_farm_metrics.py",
]

LEADERBOARD = "aggregates/load_fact_farm_leaderboard.py"


def _task_id(script):
    """dimensions/load_dim_farm.py -> load_dim_farm."""
    return script.rsplit("/", 1)[-1].removesuffix(".py")


def _submit(script):
    """Build a SparkSubmitOperator for one loader script."""
    return SparkSubmitOperator(
        task_id=_task_id(script),
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
    default_args={"retries": 1},
    tags=["module-3", "warehouse", "spark", "clickhouse"],
)
def warehouse_load():
    dims_done = EmptyOperator(task_id="dims_done")
    facts_done = EmptyOperator(task_id="facts_done")
    aggs_done = EmptyOperator(task_id="aggs_done")

    dims = {op.task_id: op for op in (_submit(s) for s in DIMENSIONS)}
    user_farm_role = _submit(USER_FARM_ROLE)
    facts = [_submit(s) for s in FACTS]
    aggs = [_submit(s) for s in AGGREGATES]
    leaderboard = _submit(LEADERBOARD)

    # dim_user_farm_role reads dim_user / dim_role / dim_farm, so it waits on
    # them instead of running in the parallel dims bucket.
    for parent in USER_FARM_ROLE_PARENTS:
        dims[parent] >> user_farm_role

    # The dims phase is complete only once the parallel dims and the dependent
    # dim_user_farm_role have all finished.
    list(dims.values()) >> dims_done
    user_farm_role >> dims_done

    dims_done >> facts
    facts >> facts_done >> aggs
    aggs >> aggs_done >> leaderboard


warehouse_load()
