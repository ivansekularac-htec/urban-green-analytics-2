"""DAG factory: one incremental-extract DAG per ``app.*`` table.

Tables and their schedules come from ``extract.config.TABLES``; the extraction
logic lives in ``extract.extractor``. Adding or removing a table is a one-line
change in the registry - no per-table DAG code.

``harvests`` runs hourly and is partitioned on disk by the harvest's own date;
the other 12 tables run daily as a single object per run.
"""

from __future__ import annotations

import os
import sys

import pendulum
from airflow.sdk import dag, task

# The sibling ``extract`` package lives in the dags folder, which isn't always on
# sys.path (e.g. under `airflow dags test`). Add it explicitly so the imports
# below resolve in every context - no compose changes needed.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract.config import TABLES  # noqa: E402
from extract.extractor import run_extract  # noqa: E402


def _build_extract_dag(cfg: dict):
    table = cfg["name"]
    partition_by = cfg.get("partition_by")
    partition_label = cfg.get("partition_label")

    @dag(
        dag_id=f"extract_{table}",
        schedule=cfg["schedule"],
        start_date=pendulum.datetime(
            2024,
            1,
            1,
            tz="UTC",
        ),
        catchup=False,
        # Cursor is shared state - never let two runs of the same table overlap.
        max_active_runs=1,
        # Retry once to ride out a transient Postgres/MinIO blip.
        default_args={"retries": 1},
        tags=["extract", "staging"],
    )
    def _extract_dag():
        @task(task_id="extract")
        def extract() -> None:
            run_extract(table, partition_by, partition_label)

        extract()

    return _extract_dag()


for _cfg in TABLES:
    globals()[f"extract_{_cfg['name']}"] = _build_extract_dag(_cfg)
