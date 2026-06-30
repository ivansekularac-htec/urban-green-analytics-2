"""
Runtime configuration for the ingestion pipeline.

Loads:
- Environment configuration
- Static table metadata from YAML
"""

import os
from pathlib import Path

import yaml

# ---------------------------------------------------------
# Connections
# ---------------------------------------------------------

POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "urbangreen_db")
MINIO_CONN_ID = os.getenv("MINIO_CONN_ID", "urbangreen_minio")

# ---------------------------------------------------------
# Extraction
# ---------------------------------------------------------

CURSOR_SAFETY_WINDOW_SECONDS = os.getenv("CURSOR_SAFETY_WINDOW_SECONDS", "30")
INGESTION_CHUNK_SIZE = int(os.getenv("INGESTION_CHUNK_SIZE", "10000"))

# ---------------------------------------------------------
# Storage
# ---------------------------------------------------------

STAGING_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")
OBJECT_PREFIX = "raw/postgres"

# ---------------------------------------------------------
# Table metadata
# ---------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "table_configs.yaml"

with CONFIG_PATH.open() as f:
    TABLE_CONFIGS = yaml.safe_load(f)["tables"]

# Inject runtime bucket into every table config.
for table in TABLE_CONFIGS:
    table["bucket"] = STAGING_BUCKET
