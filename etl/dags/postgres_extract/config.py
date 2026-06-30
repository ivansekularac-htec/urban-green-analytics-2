"""
config.py
Configuration for PostgreSQL-to-MinIO extraction DAGs.

This module defines Airflow connection identifiers, source and destination
settings, and loads table extraction configuration from YAML.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

POSTGRES_CONN_ID = os.getenv("POSTGRES_EXTRACT_CONN_ID", "urbangreen_db")
MINIO_CONN_ID = os.getenv("MINIO_EXTRACT_CONN_ID", "urbangreen_minio")
POSTGRES_SCHEMA = os.getenv("POSTGRES_EXTRACT_SCHEMA", "app")
STAGING_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")

TABLE_CONFIG_FILE = Path(__file__).with_name("table_configs.yaml")

HARVESTS_CHUNK_SIZE = int(os.getenv("HARVESTS_EXTRACT_CHUNK_SIZE", "50000"))

if HARVESTS_CHUNK_SIZE <= 0:
    raise ValueError("HARVESTS_EXTRACT_CHUNK_SIZE must be greater than zero.")


def _load_table_configs() -> list[dict[str, Any]]:
    """
    Load table extraction configuration from the YAML config file.
    """
    with TABLE_CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Table config file must contain a YAML object.")

    table_configs = config.get("tables")

    if not isinstance(table_configs, list):
        raise ValueError("Table config file must contain a 'tables' list.")

    return table_configs


def _apply_runtime_overrides(
    table_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Apply environment-driven overrides to loaded table configurations.
    """
    for table_config in table_configs:
        if table_config["table"] == "harvests":
            table_config["chunk_size"] = HARVESTS_CHUNK_SIZE

    return table_configs


TABLE_CONFIGS = _apply_runtime_overrides(_load_table_configs())
