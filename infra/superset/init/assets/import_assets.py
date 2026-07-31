"""
Imports Urban Green Superset assets.

This module imports the exported Superset assets bundle containing
databases, datasets, charts and dashboards.
"""

import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_PATH = Path(__file__).parent / "dashboards.zip"

IMPORT_USERNAME = os.environ.get(
    "SUPERSET_ADMIN_USERNAME",
    "admin",
)


def inject_database_password():
    """Replace masked ClickHouse password in exported assets."""

    password = os.environ["CLICKHOUSE_PASSWORD"]

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(ASSETS_PATH, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        for yaml_file in Path(tmpdir).rglob("*.yaml"):
            content = yaml_file.read_text()

            if "sqlalchemy_uri:" in content and "XXXXXXXXXX" in content:
                yaml_file.write_text(content.replace("XXXXXXXXXX", password))

        new_zip = Path(tmpdir) / "dashboards_new.zip"

        with zipfile.ZipFile(new_zip, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for file in Path(tmpdir).rglob("*"):
                if file == new_zip or file.is_dir():
                    continue
                zip_ref.write(file, file.relative_to(tmpdir))

        shutil.move(new_zip, ASSETS_PATH)


def publish_dashboards():
    """Publish all imported dashboards."""

    from superset.extensions import db
    from superset.models.dashboard import Dashboard

    for dashboard in db.session.query(Dashboard).all():
        dashboard.published = True

    db.session.commit()

    logger.info("Published all dashboards.")


def import_assets():
    """Import the exported Superset assets bundle."""

    if not ASSETS_PATH.exists():
        raise FileNotFoundError(f"Assets archive not found: {ASSETS_PATH}")

    logger.info(f"Importing assets from '{ASSETS_PATH}'.")

    inject_database_password()

    subprocess.run(
        [
            "superset",
            "import-dashboards",
            "--path",
            str(ASSETS_PATH),
            "--username",
            IMPORT_USERNAME,
        ],
        check=True,
    )

    logger.info("Successfully imported Superset assets.")
