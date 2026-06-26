from __future__ import annotations

import pendulum
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

from extract_common.extractor import extract_table_to_minio
from extract_common.table_config import APP_TABLES, ExtractTable

DEFAULT_ARGS = {
    "owner": "urbangreen",
    "retries": 1,
}


def build_extract_dag(table: ExtractTable) -> DAG:
    """Build one low-touch extract DAG from table configuration."""
    dag_id = f"extract_app_{table.name}_to_minio"

    with DAG(
        dag_id=dag_id,
        description=f"Incrementally extract app.{table.name} from Postgres to MinIO staging Parquet.",
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        schedule=table.schedule,
        catchup=False,
        max_active_runs=1,
        default_args=DEFAULT_ARGS,
        tags=["urbangreen", "postgres", "minio", "staging", "extract"],
    ) as dag:
        PythonOperator(
            task_id=f"extract_{table.name}",
            python_callable=extract_table_to_minio,
            op_kwargs={"table_config": table.to_dict()},
            show_return_value_in_logs=False,
        )

    return dag


for extract_table in APP_TABLES:
    generated_dag = build_extract_dag(extract_table)
    globals()[generated_dag.dag_id] = generated_dag
