"""Shared state schema and constants for the executive report pipeline."""

from __future__ import annotations

import os
from typing import Any, TypedDict

CLICKHOUSE_CONN_ID = "urbangreen_clickhouse"
MINIO_CONN_ID = "urbangreen_minio"
SMTP_CONN_ID = "urbangreen_smtp"
STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")
OBJECT_KEY_TEMPLATE = "reports/executive/date={report_date}/report.html"


class ReportState(TypedDict, total=False):
    report_date: str
    kpis: dict[str, Any]
    narrative: str
    insights: list[str]
    html: str
    object_key: str
