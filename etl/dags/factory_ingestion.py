from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from ingestion.config import TABLE_CONFIGS
from ingestion.extract import extract_table


def create_table_dag(config):
    """
    Factory function that creates an Airflow DAG for a single database table.

    Each generated DAG is responsible for:
    - Extracting incremental data from a specific Postgres table
    - Writing data to MinIO as Parquet files
    - Maintaining an incremental cursor per table
    - Providing a runnable, isolated ingestion unit in the Airflow UI

    Args:
        config (dict):
            Configuration dictionary defining table ingestion behavior.
            Expected keys:
                - table (str): Table name in Postgres schema
                - schema (str): Database schema name
                - cursor_column (str): Column used for incremental extraction
                - bucket (str): Target MinIO bucket name
                - schedule (str): Airflow schedule interval (@daily, @hourly, etc.)

    Returns:
        str:
            The generated DAG ID for registration in Airflow.

    Notes:
        - Each table results in its own independent DAG
        - DAGs are dynamically generated at import time
        - All ingestion logic is delegated to extract_table()
    """

    table = config["table"]
    dag_id = f"extract_{table}"

    with DAG(
        dag_id=dag_id,
        start_date=datetime(2026, 1, 1),
        schedule=config["schedule"],
        catchup=False,
        tags=["ingestion", table],
    ):

        @task
        def run():
            """
            Executes the ingestion process for a single table.

            Steps:
            - Reads incremental cursor from Airflow Variables
            - Extracts new rows from Postgres
            - Writes data to MinIO as Parquet
            - Updates cursor after successful ingestion
            - Returns structured execution result
            """
            try:
                result = extract_table(config)
            except Exception as e:
                result = {
                    "table": table,
                    "status": "FAILED",
                    "error": str(e),
                }

            print(f"[{table}] {result}")
            return result

        run()

    return dag_id


# -------------------------
# DAG REGISTRATION
# -------------------------

for config in TABLE_CONFIGS:
    globals()[f"dag_{config['table']}"] = create_table_dag(config)
