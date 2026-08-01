"""
Bootstraps the Urban Green Superset environment.

The bootstrap process:

1. imports Superset assets
2. assigns imported assets to business roles
3. creates business roles
4. provisions users
5. synchronizes Row-Level Security policies
"""

import logging

from assets.import_assets import import_assets
from superset.app import create_app
from users.asign_assets import assign_assets
from users.create_rls import create_or_update_rls
from users.create_roles import create_roles
from users.create_users import create_users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def bootstrap():
    """Bootstrap Urban Green Superset configuration."""

    app = create_app()

    with app.app_context():
        import_assets()
        create_roles(app)
        create_users(app)
        assign_assets(app)
        create_or_update_rls(app)


if __name__ == "__main__":
    bootstrap()
