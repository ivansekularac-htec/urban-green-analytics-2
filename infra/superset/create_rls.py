from superset import db
from superset.app import create_app

RLS_NAME = "Farm Access"

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

    existing = (
        db.session.query(RowLevelSecurityFilter)
        .filter(RowLevelSecurityFilter.name == RLS_NAME)
        .first()
    )

    if existing:
        print(f"RLS rule '{RLS_NAME}' already exists. Skipping.")
        exit(0)

    roles = (
        db.session.query(Role)
        .filter(Role.name.in_(["FarmManager", "OperationsTeam"]))
        .all()
    )

    if len(roles) != 2:
        raise RuntimeError("FarmManager and OperationsTeam roles must exist.")

    datasets = db.session.query(SqlaTable).all()

    farm_datasets = []

    for dataset in datasets:
        columns = {column.column_name for column in dataset.columns}

        if "farm_id" in columns:
            farm_datasets.append(dataset)

    if not farm_datasets:
        raise RuntimeError("No datasets with farm_id column found.")

    print("Applying RLS to:")

    for dataset in farm_datasets:
        print(f"- {dataset.table_name}")

    rls = RowLevelSecurityFilter(
        name=RLS_NAME,
        filter_type="Regular",
        clause=CLAUSE,
    )

    rls.roles = roles
    rls.tables = farm_datasets

    db.session.add(rls)
    db.session.commit()

    print(f"Created RLS rule '{RLS_NAME}' for {len(farm_datasets)} datasets.")
