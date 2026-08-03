"""
Dashboard ZIP import and ClickHouse credential reconciliation.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from urllib.parse import quote_plus
from zipfile import ZipFile, is_zipfile

from .bootstrap_common import (
    CLICKHOUSE_DATABASE_NAME,
    bump,
    env,
    get_database,
    logger,
)

DASHBOARD_BUNDLE_PATH = Path(
    os.environ.get(
        "SUPERSET_DASHBOARD_BUNDLE",
        "/app/exports/dashboards_export.zip",
    )
)
BUNDLE_HASH_PATH = Path("/app/superset_home/.dashboard_bundle.sha256")

# Matches databases/*.yaml path inside the export after root strip.
CLICKHOUSE_DATABASE_YAML = "databases/ClickHouse_Connect_Superset.yaml"


def _bundle_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clickhouse_sqlalchemy_uri() -> str:
    user = quote_plus(env("CLICKHOUSE_USER", "urbangreen"))
    password = quote_plus(env("CLICKHOUSE_PASSWORD"))
    host = env("CLICKHOUSE_HOST", "urbangreen-clickhouse")
    port = env("CLICKHOUSE_HTTP_PORT", "8123")
    database = env("CLICKHOUSE_DB", "urbangreen_dw")
    return f"clickhousedb+connect://{user}:{password}@{host}:{port}/{database}"


def import_dashboard_bundle() -> None:
    """Import the committed dashboard ZIP (DB/datasets/charts/dashboards)."""
    from flask import g
    from superset import security_manager
    from superset.commands.dashboard.importers.dispatcher import ImportDashboardsCommand
    from superset.commands.importers.v1.utils import get_contents_from_bundle

    if not DASHBOARD_BUNDLE_PATH.is_file():
        raise RuntimeError(
            f"Dashboard bundle not found at {DASHBOARD_BUNDLE_PATH}. "
            "Copy infra/superset/exports into the image."
        )
    if not is_zipfile(DASHBOARD_BUNDLE_PATH):
        raise RuntimeError(f"{DASHBOARD_BUNDLE_PATH} is not a valid ZIP file")

    digest = _bundle_sha256(DASHBOARD_BUNDLE_PATH)
    if BUNDLE_HASH_PATH.is_file() and BUNDLE_HASH_PATH.read_text().strip() == digest:
        logger.info(
            "Dashboard bundle unchanged (%s); import skipped",
            DASHBOARD_BUNDLE_PATH.name,
        )
        bump("skipped")
        return

    admin_username = env("SUPERSET_ADMIN_USERNAME", "admin")
    admin = security_manager.find_user(username=admin_username)
    if admin is None:
        raise RuntimeError(
            f"Admin user {admin_username!r} missing; cannot import dashboards."
        )
    g.user = admin

    clickhouse_password = env("CLICKHOUSE_PASSWORD")
    passwords = {CLICKHOUSE_DATABASE_YAML: clickhouse_password}

    with ZipFile(DASHBOARD_BUNDLE_PATH) as bundle:
        contents = get_contents_from_bundle(bundle)

    # overwrite=True updates dashboards; child objects match by UUID (no dupes).
    ImportDashboardsCommand(
        contents,
        overwrite=True,
        passwords=passwords,
    ).run()

    BUNDLE_HASH_PATH.write_text(digest + "\n")
    logger.info(
        "Dashboard bundle imported from %s",
        DASHBOARD_BUNDLE_PATH.name,
    )
    bump("updated")


def reconcile_clickhouse_connection() -> None:
    """Update the imported ClickHouse URI/password from environment variables."""
    from superset import db

    database = get_database()
    if database is None:
        raise RuntimeError(
            f"ClickHouse connection {CLICKHOUSE_DATABASE_NAME!r} not found after "
            "dashboard import. Check the export bundle."
        )

    desired_uri = _clickhouse_sqlalchemy_uri()
    current = database.sqlalchemy_uri_decrypted
    if current == desired_uri:
        logger.info("ClickHouse connection credentials skipped")
        bump("skipped")
        return

    database.set_sqlalchemy_uri(desired_uri)
    db.session.commit()
    logger.info("ClickHouse connection credentials updated")
    bump("updated")
