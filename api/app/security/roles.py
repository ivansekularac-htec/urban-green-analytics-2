"""
Role names used for authorization checks.

Single source of truth — the string values must match the ``roles.name``
column populated by ``infra/postgres/init/02_seed.sql``.
"""

from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "Admin"
    FARM_MANAGER = "Farm Manager"
    OPERATIONS_TEAM = "Operations Team"
