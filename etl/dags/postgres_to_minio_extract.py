"""
postgres_to_minio_extract.py

Dynamic Airflow DAG definitions for PostgreSQL-to-MinIO extraction.

This module creates one extraction DAG for every table defined in
TABLE_CONFIGS. Small tables run daily, while the harvests table runs hourly.
"""

from __future__ import annotations

from typing import Any

import pendulum
from airflow.sdk import dag, task
from postgres_extract.config import TABLE_CONFIGS
from postgres_extract.extract import extract_table_to_minio


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


for config in TABLE_CONFIGS:
    dag_name = f"extract_postgres_{config['table']}_to_minio"
    globals()[dag_name] = build_extract_dag(config)
