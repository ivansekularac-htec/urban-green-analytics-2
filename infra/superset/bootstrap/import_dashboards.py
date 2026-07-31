import os
from zipfile import ZipFile

from flask import g
from superset.app import create_app

app = create_app()


def main():
    with app.app_context():
        from superset.commands.dashboard.importers.dispatcher import (
            ImportDashboardsCommand,
        )
        from superset.commands.importers.v1.utils import (
            get_contents_from_bundle,
        )

        security_manager = app.appbuilder.sm

        admin = security_manager.find_user(
            username=os.environ["SUPERSET_ADMIN_USERNAME"]
        )

        g.user = admin

        with ZipFile("/app/dashboards_export.zip") as bundle:
            contents = get_contents_from_bundle(bundle)

        db_yaml = next(
            key
            for key in contents
            if key.startswith("databases/") and key.endswith(".yaml")
        )

        ImportDashboardsCommand(
            contents,
            overwrite=True,
            passwords={
                db_yaml: os.environ["CLICKHOUSE_PASSWORD"],
            },
        ).run()


if __name__ == "__main__":
    main()
