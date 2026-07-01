from datetime import timedelta
from pathlib import Path

import pendulum
import yaml
from airflow import DAG
from airflow.operators.python import PythonOperator
from ingestion.extract import extract_and_write

# ---------------------------------------------------------
# Load table configuration
# ---------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parent / "ingestion" / "tables.yaml"

with open(CONFIG_PATH, "r") as f:
    configs = yaml.safe_load(f)["tables"]

# ---------------------------------------------------------
# Create one DAG per table
# ---------------------------------------------------------

for config in configs:
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

    # Register DAG so Airflow discovers it
    globals()[dag.dag_id] = dag
