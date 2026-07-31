"""
Create or update the "Farm Access" Row-Level Security rule.
The rule uses the dim_user_farm_role mapping to filter datasets so
users only see data for their assigned farms.
"""

import logging

from superset import db
from superset.app import create_app

logger = logging.getLogger(__name__)

RLS_NAME = "Farm Access"

# Grant access to all farms for users with a global assignment (farm_id = 0).
# Otherwise, restrict access to the farms explicitly assigned to the user.
CLAUSE = """
(
    EXISTS (
        SELECT 1
        FROM dim_user_farm_role FINAL ur
        JOIN dim_user FINAL u
          ON u.user_id = ur.user_id
        WHERE u.email = '{{ current_user.email }}'
          AND ur.farm_id = 0
    )
    OR
    farm_id IN (
        SELECT ur.farm_id
        FROM dim_user_farm_role FINAL ur
        JOIN dim_user FINAL u
          ON u.user_id = ur.user_id
        WHERE u.email = '{{ current_user.email }}'
    )
)
"""


app = create_app()

with app.app_context():
    from flask_appbuilder.security.sqla.models import Role
    from superset.connectors.sqla.models import RowLevelSecurityFilter, SqlaTable

    # Apply the RLS rule to the demo roles used by the dashboards.
    roles = (
        db.session.query(Role)
        .filter(Role.name.in_(["FarmManager", "OperationsTeam"]))
        .all()
    )

    if len(roles) != 2:
        raise RuntimeError("FarmManager and OperationsTeam roles must exist.")

    # Protect every dataset with the same farm-level access rule.
    datasets = db.session.query(SqlaTable).all()

    if not datasets:
        raise RuntimeError("No datasets found.")

    # Reuse the existing RLS rule if it has already been created.
    rls = (
        db.session.query(RowLevelSecurityFilter)
        .filter(RowLevelSecurityFilter.name == RLS_NAME)
        .first()
    )

    if rls:
        logger.info(
            "RLS rule '%s' already exists. Updating assignments.",
            RLS_NAME,
        )

        rls.roles = roles
        rls.tables = datasets

        # Keep the SQL clause synchronized with the latest definition.
        rls.clause = CLAUSE

    else:
        logger.info(
            "Creating RLS rule '%s'.",
            RLS_NAME,
        )

        rls = RowLevelSecurityFilter(
            name=RLS_NAME,
            filter_type="Regular",
            clause=CLAUSE,
        )

        # Assign the new RLS rule to every dataset and supported role.
        rls.roles = roles
        rls.tables = datasets

        db.session.add(rls)

    db.session.commit()

    logger.info(
        "RLS rule '%s' applied to %s datasets and %s roles.",
        RLS_NAME,
        len(datasets),
        len(roles),
    )
