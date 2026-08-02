"""
Assigns imported Superset assets to Urban Green business roles.

This module applies post-import configuration to Superset assets by:

- publishing imported dashboards
- assigning dashboard access to business roles
- assigning datasource access to business roles

This keeps asset import idempotent while ensuring imported resources
are immediately accessible to authorized users.
"""

import logging

from users.common import DASHBOARD_ROLE_MAPPING, DATASET_ROLE_MAPPING

logger = logging.getLogger(__name__)


def assign_assets(app):
    """Assign imported dashboards and datasets to business roles."""
    from superset.connectors.sqla.models import SqlaTable
    from superset.extensions import db
    from superset.models.dashboard import Dashboard

    sm = app.appbuilder.sm

    for dashboard in db.session.query(Dashboard).all():
        dashboard.published = True

        role_names = DASHBOARD_ROLE_MAPPING.get(dashboard.dashboard_title)

        if role_names is None:
            logger.warning(
                f"No dashboard role mapping for '{dashboard.dashboard_title}'."
            )
            continue

        dashboard.roles = [
            sm.find_role(role_name)
            for role_name in role_names
            if sm.find_role(role_name) is not None
        ]

        logger.info(
            "Dashboard '%s' -> %s",
            dashboard.dashboard_title,
            [r.name for r in dashboard.roles],
        )

    for dataset in db.session.query(SqlaTable).all():
        role_names = DATASET_ROLE_MAPPING.get(dataset.table_name)

        if role_names is None:
            logger.warning(f"No dataset role mapping for '{dataset.table_name}'.")
            continue

        dataset.roles = [
            sm.find_role(role_name)
            for role_name in role_names
            if sm.find_role(role_name) is not None
        ]

    db.session.commit()

    logger.info("Assigned dashboards and datasets.")
