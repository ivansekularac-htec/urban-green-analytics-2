"""DAG factory that builds one extract_<table> DAG per entry in tables.yaml."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import yaml
from airflow.sdk import dag, task

_DAGS_DIR = str(Path(__file__).resolve().parent)
if _DAGS_DIR not in sys.path:
    sys.path.insert(0, _DAGS_DIR)

from postgres_extract.extract import run_extract  # noqa: E402

_TABLES_YAML = Path(__file__).resolve().parent / "postgres_extract" / "tables.yaml"


def _load_tables():
    """Load the table registry from YAML, merging defaults into each entry."""
    raw = yaml.safe_load(_TABLES_YAML.read_text())
    defaults = raw.get("defaults", {})
    return [{**defaults, **entry} for entry in raw.get("tables", [])]


def _build_dag(cfg):
    """Build one extract DAG from a single table config entry."""
    table = cfg["name"]
    partition_by = cfg.get("partition_by")
    partition_label = cfg.get("partition_label")

    @dag(
        dag_id=f"extract_{table}",
        schedule=cfg["schedule"],
        start_date=datetime(2024, 1, 1),
        catchup=False,
        max_active_runs=1,
        default_args={"retries": 1},
        tags=["extract", "postgres"],
    )
    def _dag():
        @task(task_id="extract")
        def extract():
            run_extract(table, partition_by, partition_label)

        extract()

    return _dag()


for _cfg in _load_tables():
    globals()[f"extract_{_cfg['name']}"] = _build_dag(_cfg)
