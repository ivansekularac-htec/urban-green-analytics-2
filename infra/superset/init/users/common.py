"""
Shared constants and helper functions.
"""

import os

import clickhouse_connect

CLICKHOUSE_CONFIG = {
    "host": os.environ["CLICKHOUSE_HOST"],
    "port": int(os.environ["CLICKHOUSE_HTTP_PORT"]),
    "database": os.environ["CLICKHOUSE_DB"],
    "username": os.environ["CLICKHOUSE_USER"],
    "password": os.environ["CLICKHOUSE_PASSWORD"],
}

SUPERSET_DATABASE_NAME = "Urban Green DW"


BUSINESS_ROLES = [
    "FarmManager",
    "Operations",
]

ROLE_MAPPING = {
    "Admin": "Admin",
    "Farm Manager": "FarmManager",
    "Operations Team": "Operations",
}

RLS_ROLE_PREFIX = "RLS_USER"
RLS_FILTER_PREFIX = "Farm Access"


def get_rls_role_name(user_id):
    """Return the dedicated RLS role name for a user."""
    return f"{RLS_ROLE_PREFIX}_{user_id}"


def get_rls_filter_name(user_id):
    """Return the RLS filter name for a user."""
    return f"{RLS_FILTER_PREFIX} - {user_id}"


def get_clickhouse_client():
    """Return a ClickHouse client."""
    return clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)


def execute_query(sql):
    """Execute a SQL query against ClickHouse and return named results."""
    return get_clickhouse_client().query(sql).named_results()
