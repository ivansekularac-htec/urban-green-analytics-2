"""
UrbanGreen Superset bootstrap orchestrator.

Startup (via init-superset.sh):
  python -m bootstrap.bootstrap_security --ensure-admin-only
  python -m bootstrap.bootstrap_security
"""

from __future__ import annotations

import argparse

from superset.app import create_app

from .bootstrap_common import logger, print_summary
from .bootstrap_import import import_dashboard_bundle, reconcile_clickhouse_connection
from .bootstrap_rbac import (
    ensure_admin,
    ensure_custom_roles,
    ensure_dashboard_permissions,
    ensure_dataset_permissions,
    ensure_demo_users,
)
from .bootstrap_rls import ensure_farm_rls


def run_ensure_admin_only() -> None:
    logger.info("Starting admin-only bootstrap...")
    app = create_app()
    with app.app_context():
        ensure_admin()
        print_summary()
    logger.info("Admin-only bootstrap completed.")


def run_full_bootstrap() -> None:
    logger.info("Starting full Superset bootstrap...")
    app = create_app()
    with app.app_context():
        ensure_admin()
        ensure_custom_roles()
        ensure_demo_users()
        import_dashboard_bundle()
        reconcile_clickhouse_connection()
        ensure_dataset_permissions()
        ensure_dashboard_permissions()
        ensure_farm_rls()
        print_summary()
    logger.info("Full Superset bootstrap completed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="UrbanGreen Superset bootstrap")
    parser.add_argument(
        "--ensure-admin-only",
        action="store_true",
        help="Only ensure the Admin user exists (run before `superset init`).",
    )
    args = parser.parse_args()

    if args.ensure_admin_only:
        run_ensure_admin_only()
    else:
        run_full_bootstrap()


if __name__ == "__main__":
    main()
