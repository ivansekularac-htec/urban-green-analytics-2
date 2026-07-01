from datetime import timedelta
from pathlib import Path

import pendulum
import yaml
from airflow import DAG
from airflow.operators.python import PythonOperator
from ingestion.extract import extract_and_write

# ---------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parent / "ingestion" / "tables.yaml"

with open(CONFIG_PATH, "r") as f:
    configs = yaml.safe_load(f)["tables"]


def build_dag(config: dict) -> DAG:
    """
    Builds a single Airflow DAG for a given table configuration.

    Each DAG represents an incremental extraction pipeline:
    Postgres → chunked extraction → MinIO (Parquet).

    Args:
        config (dict): Table configuration containing:
            - table (str): table name
            - schedule (str): Airflow schedule expression
            - schema (str): Postgres schema
            - cursor_column (str): incremental column
            - partition_column (str | None): optional partition column

    Returns:
        DAG: Fully configured Airflow DAG instance
    """

    table = config["table"]
    schedule = config["schedule"]

    dag = DAG(
        dag_id=f"extract_{table}",
        description=f"Incrementally extract {table} from Postgres to MinIO",
        schedule=schedule,
        start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
        catchup=False,
        default_args={
            "owner": "airflow",
            "retries": 1,
            "retry_delay": timedelta(minutes=5),
        },
        tags=["ingestion", table],
    )

    with dag:
        PythonOperator(
            task_id="extract_and_write",
            python_callable=extract_and_write,
            op_kwargs={"config": config},
        )

    return dag


# ---------------------------------------------------------
# DAG registration (Airflow discovery point)
# ---------------------------------------------------------

for config in configs:
    dag = build_dag(config)

    # Register DAG in module scope so Airflow can discover it
    globals()[dag.dag_id] = dag
