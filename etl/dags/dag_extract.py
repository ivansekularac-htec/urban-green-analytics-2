from __future__ import annotations

from pathlib import Path
from typing import Any

import pendulum
import yaml
from airflow.sdk import DAG, task
from postgres_extract.extract import extract_table

DEFAULT_ARGS = {
    "owner": "urbangreen",
    "retries": 1,
}

TABLES_CONFIG_PATH = Path(__file__).parent / "postgres_extract" / "tables.yaml"


def load_table_configs() -> list[dict[str, Any]]:
    with TABLES_CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    return config.get("tables", [])


def build_dag(table_config: dict[str, Any]) -> DAG:
    table_name = table_config["name"]
    dag_id = f"extract_app_{table_name}_to_minio"

    with DAG(
        dag_id=dag_id,
        description=f"Extract app.{table_name} from Postgres to MinIO staging.",
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        schedule=table_config.get("schedule", "@daily"),
        catchup=False,
        max_active_runs=1,
        default_args=DEFAULT_ARGS,
        tags=["urbangreen", "postgres", "minio", "extract"],
    ) as dag:

        @task(
            task_id=f"extract_{table_name}",
            show_return_value_in_logs=False,
        )
        def run_extract(config: dict[str, Any]) -> None:
            extract_table(config)

        run_extract(table_config)

    return dag


for config in load_table_configs():
    generated_dag = build_dag(config)
    globals()[generated_dag.dag_id] = generated_dag
