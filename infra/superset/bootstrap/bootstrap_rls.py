"""
Farm Row-Level Security rule (Base filter, Admin exempt).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bootstrap_common import (
    CLICKHOUSE_DATABASE_NAME,
    EXPECTED_RLS_DATASETS,
    bump,
    get_admin_role,
    get_database,
    get_dataset,
    logger,
)

if TYPE_CHECKING:
    from superset.connectors.sqla.models import RowLevelSecurityFilter

RLS_RULE_NAME = "farm_id_by_username"
RLS_CLAUSE = (
    "farm_id IN (\n"
    "    SELECT farm_id\n"
    "    FROM v_user_farm_permissions\n"
    "    WHERE lower(username) = lower('{{ current_username() }}')\n"
    ")"
)


def _get_rls_rule(name: str = RLS_RULE_NAME) -> RowLevelSecurityFilter | None:
    from superset import db
    from superset.connectors.sqla.models import RowLevelSecurityFilter

    return (
        db.session.query(RowLevelSecurityFilter)
        .filter(RowLevelSecurityFilter.name == name)
        .one_or_none()
    )


def ensure_farm_rls() -> None:
    """Ensure exactly one Base farm RLS rule; Admin exempt; expected datasets only."""
    from superset import db
    from superset.connectors.sqla.models import RowLevelSecurityFilter
    from superset.utils.core import RowLevelSecurityFilterType

    admin_role = get_admin_role()
    database = get_database()
    if database is None:
        raise RuntimeError(
            f"ClickHouse connection {CLICKHOUSE_DATABASE_NAME!r} not found."
        )

    target_tables = []
    missing = []
    for table_name in EXPECTED_RLS_DATASETS:
        dataset = get_dataset(database, table_name)
        if dataset is None:
            missing.append(table_name)
        else:
            target_tables.append(dataset)

    if missing:
        logger.info(
            "Farm RLS datasets not yet available: %s",
            ", ".join(missing),
        )

    desired_role_ids = {admin_role.id}
    desired_table_ids = {t.id for t in target_tables}
    rls = _get_rls_rule()

    if rls is None:
        rls = RowLevelSecurityFilter(
            name=RLS_RULE_NAME,
            description=(
                "Restrict non-Admin users to farms granted in "
                "v_user_farm_permissions (username = email)."
            ),
            filter_type=RowLevelSecurityFilterType.BASE.value,
            clause=RLS_CLAUSE,
            group_key=None,
        )
        rls.roles = [admin_role]
        rls.tables = list(target_tables)
        db.session.add(rls)
        db.session.commit()
        logger.info(
            "Farm RLS %s created (attached to %s dataset(s))",
            RLS_RULE_NAME,
            len(target_tables),
        )
        bump("created")
        return

    changed = False
    if rls.filter_type != RowLevelSecurityFilterType.BASE.value:
        rls.filter_type = RowLevelSecurityFilterType.BASE.value
        changed = True
    if (rls.clause or "").strip() != RLS_CLAUSE.strip():
        rls.clause = RLS_CLAUSE
        changed = True
    if {role.id for role in rls.roles} != desired_role_ids:
        rls.roles = [admin_role]
        changed = True
    if {table.id for table in rls.tables} != desired_table_ids:
        rls.tables = list(target_tables)
        changed = True

    if changed:
        db.session.commit()
        logger.info(
            "Farm RLS %s updated (attached to %s dataset(s))",
            RLS_RULE_NAME,
            len(target_tables),
        )
        bump("updated")
    else:
        logger.info(
            "Farm RLS %s skipped (already up to date, %s dataset(s))",
            RLS_RULE_NAME,
            len(target_tables),
        )
        bump("skipped")
