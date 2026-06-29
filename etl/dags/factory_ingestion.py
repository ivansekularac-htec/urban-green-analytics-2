"""
Dynamic Airflow DAG factory for Postgres table ingestion.

This module generates one Airflow DAG per configured table defined in
``TABLE_CONFIGS``. Each DAG executes an incremental extraction from
Postgres into MinIO as Parquet while maintaining its own ingestion cursor.

Adding a new table requires only updating ``TABLE_CONFIGS``; no additional
DAG code is necessary.
"""

from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowSkipException
from ingestion.config import TABLE_CONFIGS
from ingestion.extract import extract_table


def create_table_dag(config):
    """
    Creates an Airflow DAG for a single table ingestion pipeline.

    Each generated DAG is responsible for:
        - Incrementally extracting rows from Postgres
        - Writing them to MinIO as Parquet
        - Updating the ingestion cursor after a successful write

    Args:
        config (dict):
            Table-specific ingestion configuration.

    Returns:
        str:
            Generated DAG identifier.
    """

    table = config["table"]

    with DAG(
        dag_id=f"extract_{table}",
        start_date=datetime(2026, 1, 1),
        schedule=config["schedule"],
        catchup=False,
        tags=["ingestion", table],
    ) as dag:

        @task
        def run():
            """
            Executes a single ingestion run for the configured table.

            If no new rows are available, the task is marked as SKIPPED.
            Any other exception is propagated so Airflow can apply retries
            and failure handling.
            """
            try:
                result = extract_table(config)
            except AirflowSkipException:
                raise

            print(f"[{table}] {result}")
            return result

        # Register the task within the DAG.
        run()

    return dag


# ---------------------------------------------------------
# Register one DAG per configured table.
# Airflow discovers DAGs from module-level globals.
# ---------------------------------------------------------

for config in TABLE_CONFIGS:
    dag = create_table_dag(config)
    globals()[f"dag_{config['table']}"] = dag
