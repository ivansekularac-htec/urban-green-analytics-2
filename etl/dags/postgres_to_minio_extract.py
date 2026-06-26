from __future__ import annotations

from datetime import datetime
from typing import Any

from airflow.sdk import dag, task
from postgres_extract.config import TABLE_CONFIGS
from postgres_extract.extract import extract_table_to_minio


def create_extract_dag(table_config: dict[str, Any]):
    table_name = table_config["table"]
    schedule = table_config["schedule"]

    @dag(
        dag_id=f"extract_postgres_{table_name}_to_minio",
        start_date=datetime(2024, 1, 1),
        schedule=schedule,
        catchup=False,
        tags=["extract", "postgres", "minio", "parquet"],
    )
    def extract_dag():

        @task
        def extract():
            extract_table_to_minio(table_config)

        extract()

    return extract_dag()


for config in TABLE_CONFIGS:
    globals()[f"extract_postgres_{config['table']}_to_minio"] = create_extract_dag(
        config
    )
