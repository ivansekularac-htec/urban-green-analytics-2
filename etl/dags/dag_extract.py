"""
postgres_to_minio_extract.py

Dynamic Airflow DAG definitions for PostgreSQL-to-MinIO extraction.

This module creates one extraction DAG for every table defined in
postgres_extract/tables.yaml. Small tables run daily, while the harvests table
runs hourly.
"""

from __future__ import annotations

from importlib.resources import files
from typing import Any

import pendulum
import yaml
from airflow.sdk import dag, task
from postgres_extract.extract import extract_table_to_minio


def load_table_configs() -> list[dict[str, Any]]:
    """Load table extraction configs from postgres_extract/tables.yaml."""
    config_path = files("postgres_extract").joinpath("tables.yaml")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    tables = config.get("tables")

    if not isinstance(tables, list):
        raise ValueError("Invalid table config file. Expected top-level 'tables' list.")

    return tables


def build_extract_dag(table_config: dict[str, Any]):
    """Build and return an extraction DAG for one configured source table."""
    table_name = table_config["table"]
    schedule = table_config["schedule"]

    @dag(
        dag_id=f"extract_postgres_{table_name}_to_minio",
        start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
        schedule=schedule,
        catchup=False,
        max_active_runs=1,
        tags=["extract", "postgres", "minio", "parquet"],
    )
    def extract_dag():
        """Define the extraction workflow for one PostgreSQL table."""

        @task(task_id="extract")
        def extract_table(config: dict[str, Any]) -> None:
            """Extract one PostgreSQL table to the MinIO staging bucket."""
            extract_table_to_minio(config)

        extract_table(table_config)

    return extract_dag()


for table_config in load_table_configs():
    dag_name = f"extract_postgres_{table_config['table']}_to_minio"
    globals()[dag_name] = build_extract_dag(table_config)
