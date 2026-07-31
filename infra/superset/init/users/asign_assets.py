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

logger = logging.getLogger(__name__)

BUSINESS_ROLES = [
    "Operations",
    "FarmManager",
]


def assign_assets(app):
    """Assign imported dashboards and datasets to business roles."""
    from superset.connectors.sqla.models import SqlaTable
    from superset.extensions import db
    from superset.models.dashboard import Dashboard

    sm = app.appbuilder.sm

    roles = [sm.find_role(name) for name in BUSINESS_ROLES]
    roles = [r for r in roles if r]

    for dashboard in db.session.query(Dashboard).all():
        dashboard.published = True
        dashboard.roles = roles

    for dataset in db.session.query(SqlaTable).all():
        dataset.roles = roles

    db.session.commit()

    logger.info("Assigned dashboards and datasets.")
