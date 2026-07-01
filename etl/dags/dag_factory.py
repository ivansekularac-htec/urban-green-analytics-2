from __future__ import annotations

import logging
from pathlib import Path

import pendulum
import yaml
from airflow.decorators import dag, task
from postgres_extract.cursor import (
    get_cursor,
    set_cursor,
)
from postgres_extract.extract import extract_table
from postgres_extract.write import write_table

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent / "postgres_extract"
TABLES_FILE = BASE_DIR / "tables.yaml"
START_DATE = pendulum.datetime(2026, 1, 1, tz="UTC")


def load_table_configs() -> list[dict]:
    with TABLES_FILE.open() as fp:
        doc = yaml.safe_load(fp)
    return doc["tables"]


def make_postgres_extract_dag(config: dict) -> None:
    table = config["name"]
    schedule = config["schedule"]
    partition_by = config.get("partition_by")
    partition_label = config.get("partition_label")
    dag_id = f"postgres_extract__{table}"

    @dag(
        dag_id=dag_id,
        schedule=schedule,
        start_date=START_DATE,
        catchup=False,
        tags=["postgres_extract", "postgres", "minio"],
    )
    def _dag():
        @task
        def run() -> list[str]:
            current_cursor = get_cursor(table)
            cursor_from = None
            if current_cursor and current_cursor.get("updated_at") is not None:
                cursor_from = int(current_cursor["updated_at"])

            columns, rows, watermark = extract_table(table)
            cursor_to = int(watermark["updated_at"])

            file_keys = write_table(
                table,
                columns,
                rows,
                cursor_from,
                cursor_to,
                partition_by,
                partition_label,
            )
            rows_written = len(rows)
            logger.info(
                f"extract app.{table}: {rows_written} row(s), "
                f"cursor {cursor_from if cursor_from is not None else 0} -> {cursor_to}, "
                f"{len(file_keys)} object(s) written"
            )

            set_cursor(table, watermark)

            return file_keys

        run()

    globals()[dag_id] = _dag()


for table_cfg in load_table_configs():
    make_postgres_extract_dag(table_cfg)
