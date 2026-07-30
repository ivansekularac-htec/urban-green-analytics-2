"""
Admin/demo users, custom roles, and dataset/dashboard permissions.

Custom roles (Farm Manager, Operations Team) are dashboard consumers:
they get a fixed allowlist of permissions — never a Gamma clone.
"""

from __future__ import annotations

from superset import db, security_manager

from .bootstrap_common import (
    CLICKHOUSE_DATABASE_NAME,
    EXPECTED_RLS_DATASETS,
    bump,
    env,
    get_database,
    get_dataset,
    logger,
)

ROLE_FARM_MANAGER = "Farm Manager"
ROLE_OPERATIONS_TEAM = "Operations Team"
CUSTOM_ROLES = (ROLE_FARM_MANAGER, ROLE_OPERATIONS_TEAM)

# Minimal permissions for dashboard consumers. datasource_access is granted
# separately by ensure_dataset_permissions. Add to this list only when a
# Superset 403/permission error proves something is missing.
DASHBOARD_CONSUMER_PERMISSIONS = (
    ("menu_access", "Dashboards"),
    ("can_read", "Dashboard"),
    ("can_read", "Chart"),
)

# Dashboard title -> roles that may access it (Admin included explicitly).
DASHBOARD_ROLE_ACCESS = {
    "Executive Overview": ("Admin",),
    "Operations Overview": ("Admin", ROLE_OPERATIONS_TEAM),
    "Farm Overview": ("Admin", ROLE_OPERATIONS_TEAM, ROLE_FARM_MANAGER),
    "Auditor Overview": ("Admin",),
}


def ensure_admin() -> None:
    """Create the Admin user if missing. Never overwrite an existing password."""
    username = env("SUPERSET_ADMIN_USERNAME", "admin")
    existing = security_manager.find_user(username=username)
    if existing is not None:
        logger.info("Admin user %s skipped", username)
        bump("skipped")
        return

    admin_role = security_manager.find_role("Admin")
    if admin_role is None:
        admin_role = security_manager.add_role("Admin")

    user = security_manager.add_user(
        username=username,
        first_name=env("SUPERSET_ADMIN_FIRSTNAME", "Admin"),
        last_name=env("SUPERSET_ADMIN_LASTNAME", "Admin"),
        email=env("SUPERSET_ADMIN_EMAIL", "admin@urbangreen.com"),
        role=admin_role,
        password=env("SUPERSET_ADMIN_PASSWORD"),
    )
    if user is None:
        raise RuntimeError(f"Failed to create admin user {username}")

    db.session.commit()
    logger.info("Admin user %s created", username)
    bump("created")


def _ensure_role(name: str):
    role = security_manager.find_role(name)
    if role is not None:
        logger.info("Role %s skipped", name)
        bump("skipped")
        return role

    role = security_manager.add_role(name)
    if role is None:
        raise RuntimeError(f"Failed to create role {name}")
    logger.info("Role %s created", name)
    bump("created")
    return role


def _resolve_permission(permission: str, view_menu: str):
    pv = security_manager.find_permission_view_menu(permission, view_menu)
    if pv is None:
        security_manager.add_permission_view_menu(permission, view_menu)
        pv = security_manager.find_permission_view_menu(permission, view_menu)
    return pv


def _sync_role_permissions(role, permission_pairs) -> None:
    """Reset role permissions to exactly permission_pairs (removes Gamma leftovers)."""
    desired = set()
    for permission, view_menu in permission_pairs:
        pv = _resolve_permission(permission, view_menu)
        if pv is None:
            logger.warning(
                "Could not resolve permission (%s, %s); skipped",
                permission,
                view_menu,
            )
            continue
        desired.add(pv)

    current = set(role.permissions or [])
    removed = 0
    for pv in current - desired:
        security_manager.del_permission_role(role, pv)
        removed += 1

    added = 0
    for pv in desired - current:
        security_manager.add_permission_role(role, pv)
        added += 1

    if removed or added:
        logger.info(
            "Role %s permissions reset (removed=%s added=%s total=%s)",
            role.name,
            removed,
            added,
            len(desired),
        )
        bump("updated")
    else:
        logger.info(
            "Role %s permissions already match allowlist (%s)",
            role.name,
            len(desired),
        )
        bump("skipped")


def ensure_custom_roles() -> None:
    """Create Farm Manager / Operations Team and reset them to the allowlist."""
    for name in CUSTOM_ROLES:
        role = _ensure_role(name)
        _sync_role_permissions(role, DASHBOARD_CONSUMER_PERMISSIONS)
    db.session.commit()


def ensure_demo_users() -> None:
    """Create manager/ops users on custom roles. Never reset passwords."""
    farm_manager = security_manager.find_role(ROLE_FARM_MANAGER)
    operations = security_manager.find_role(ROLE_OPERATIONS_TEAM)
    if farm_manager is None or operations is None:
        raise RuntimeError(
            "Custom roles missing. Run ensure_custom_roles before demo users."
        )

    specs = (
        {
            "email": env(
                "SUPERSET_DEMO_MANAGER_EMAIL", "manager1@urbangreen.com"
            ).lower(),
            "password": env("SUPERSET_DEMO_MANAGER_PASSWORD", "changeme"),
            "first_name": env("SUPERSET_DEMO_MANAGER_FIRSTNAME", "Farm"),
            "last_name": env("SUPERSET_DEMO_MANAGER_LASTNAME", "Manager"),
            "role": farm_manager,
        },
        {
            "email": env(
                "SUPERSET_DEMO_OPS_EMAIL", "ops1@urbangreen.com"
            ).lower(),
            "password": env("SUPERSET_DEMO_OPS_PASSWORD", "changeme"),
            "first_name": env("SUPERSET_DEMO_OPS_FIRSTNAME", "Operations"),
            "last_name": env("SUPERSET_DEMO_OPS_LASTNAME", "Team"),
            "role": operations,
        },
    )

    for spec in specs:
        email = spec["email"]
        role = spec["role"]
        existing = security_manager.find_user(username=email)
        if existing is not None:
            desired_ids = {role.id}
            current_ids = {r.id for r in (existing.roles or [])}
            if current_ids != desired_ids:
                existing.roles = [role]
                logger.info("Demo user %s roles updated to %s", email, role.name)
                bump("updated")
            else:
                logger.info("Demo user %s skipped", email)
                bump("skipped")
            continue

        user = security_manager.add_user(
            username=email,
            first_name=spec["first_name"],
            last_name=spec["last_name"],
            email=email,
            role=role,
            password=spec["password"],
        )
        if user is None:
            raise RuntimeError(f"Failed to create demo user {email}")

        logger.info("Demo user %s created with role %s", email, role.name)
        bump("created")

    db.session.commit()


def _ensure_permission(role, permission: str, view_menu: str) -> str:
    pv = _resolve_permission(permission, view_menu)
    if pv is None:
        logger.warning(
            "Could not resolve permission (%s, %s); skipped",
            permission,
            view_menu,
        )
        return "skipped"

    if pv in (role.permissions or []):
        return "skipped"

    security_manager.add_permission_role(role, pv)
    return "created"


def _custom_roles():
    roles = []
    for name in CUSTOM_ROLES:
        role = security_manager.find_role(name)
        if role is None:
            raise RuntimeError(f"Role {name!r} not found.")
        roles.append(role)
    return roles


def ensure_dataset_permissions() -> None:
    """Grant custom roles datasource_access on expected farm-scoped datasets."""
    database = get_database()
    if database is None:
        raise RuntimeError(
            f"ClickHouse connection {CLICKHOUSE_DATABASE_NAME!r} not found."
        )

    roles = _custom_roles()
    for table_name in EXPECTED_RLS_DATASETS:
        dataset = get_dataset(database, table_name)
        if dataset is None:
            logger.info(
                "Dataset permission for %s skipped (not imported yet)",
                table_name,
            )
            bump("skipped")
            continue

        if not dataset.perm:
            db.session.refresh(dataset)
        if not dataset.perm:
            logger.warning(
                "Dataset %s has no perm string; skipped",
                table_name,
            )
            bump("skipped")
            continue

        for role in roles:
            result = _ensure_permission(role, "datasource_access", dataset.perm)
            if result == "created":
                logger.info(
                    "%s datasource_access for %s created",
                    role.name,
                    table_name,
                )
                bump("created")
            else:
                logger.info(
                    "%s datasource_access for %s skipped",
                    role.name,
                    table_name,
                )
                bump("skipped")

    db.session.commit()


def ensure_dashboard_permissions() -> None:
    """Assign dashboard roles per access matrix (idempotent)."""
    from superset.models.dashboard import Dashboard

    for title, role_names in DASHBOARD_ROLE_ACCESS.items():
        dashboard = (
            db.session.query(Dashboard)
            .filter(Dashboard.dashboard_title == title)
            .one_or_none()
        )
        if dashboard is None:
            logger.info("Dashboard %r skipped (not imported yet)", title)
            bump("skipped")
            continue

        desired_roles = []
        for name in role_names:
            role = security_manager.find_role(name)
            if role is None:
                raise RuntimeError(f"Role {name!r} not found for dashboard {title!r}.")
            desired_roles.append(role)

        desired_ids = {r.id for r in desired_roles}
        current_ids = {r.id for r in (dashboard.roles or [])}
        if current_ids == desired_ids:
            logger.info("Dashboard %r roles skipped", title)
            bump("skipped")
            continue

        dashboard.roles = desired_roles
        logger.info(
            "Dashboard %r roles updated to [%s]",
            title,
            ", ".join(role_names),
        )
        bump("updated")

    db.session.commit()
