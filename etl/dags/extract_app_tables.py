"""DAG factory: one incremental-extract DAG per ``app.*`` table.

The table registry is **configuration as data** — it lives in
``extract/tables.yaml``, not in Python. This factory loads that YAML, applies
the ``defaults`` block, and builds one ``extract_<table>`` TaskFlow DAG per
entry. The extraction logic itself lives in ``extract.extractor``.

``harvests`` runs hourly and is partitioned on disk by the harvest's own date;
the other tables run daily as a single object per run.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from airflow.sdk import dag, task

# The sibling ``extract`` package lives in the dags folder, which isn't always on
# sys.path (e.g. under `airflow dags test`). Add it explicitly so the import below
# resolves in every context.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract.extractor import run_extract  # noqa: E402

_TABLES_YAML = Path(__file__).resolve().parent / "extract" / "tables.yaml"


def _load_tables() -> list[dict]:
    """Load the table registry from YAML and apply the ``defaults`` block."""
    raw = yaml.safe_load(_TABLES_YAML.read_text())
    defaults = raw.get("defaults", {})
    tables: list[dict] = []
    for entry in raw.get("tables", []):
        merged = {**defaults, **entry}  # per-table values override defaults
        if "name" not in merged:
            raise ValueError(f"Table entry missing 'name': {entry}")
        if "schedule" not in merged:
            raise ValueError(f"Table {merged['name']!r} has no schedule (and no default).")
        tables.append(merged)
    return tables


TABLES = _load_tables()


def _build_extract_dag(cfg: dict):
    table = cfg["name"]
    partition_by = cfg.get("partition_by")
    partition_label = cfg.get("partition_label")

    @dag(
        dag_id=f"extract_{table}",
        schedule=cfg["schedule"],
        start_date=datetime(2024, 1, 1),
        catchup=False,
        # Cursor is shared state — never let two runs of the same table overlap.
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
