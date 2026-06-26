from __future__ import annotations

import os
from typing import Final

POSTGRES_CONN_ID: Final[str] = os.getenv("POSTGRES_EXTRACT_CONN_ID", "urbangreen_db")
MINIO_CONN_ID: Final[str] = os.getenv("MINIO_CONN_ID", "urbangreen_minio")

MINIO_STAGING_BUCKET: Final[str] = os.getenv("MINIO_STAGING_BUCKET", "staging")
MINIO_STAGING_PREFIX: Final[str] = os.getenv(
    "MINIO_STAGING_PREFIX",
    "staging/postgres/app",
).strip("/")

EXTRACT_SAFETY_LAG_SECONDS: Final[int] = int(os.getenv("EXTRACT_SAFETY_LAG_SECONDS", "2"))

DEFAULT_CURSOR: Final[dict[str, int]] = {"updated_at": 0, "id": 0}