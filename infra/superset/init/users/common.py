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

DASHBOARD_ROLE_MAPPING = {
    "Executive Overview Dashboard": ["Admin"],
    "Operations Overview Dashboard": ["Admin", "Operations"],
    # "Farm Manager Overview Dashboard": ["Admin", "FarmManager"],
}

DATASET_ROLE_MAPPING = {
    "vw_exec_overview": ["Admin"],
    "vw_exec_harvest": ["Admin"],
    "exec_top_crop_per_city": ["Admin"],
    "exec_profitability_index": ["Admin"],
    "vw_ops_leaderboard": ["Admin", "Operations"],
    "vw_ops_sensor_anomalies": ["Admin", "Operations"],
    "vw_ops_crop_yield": ["Admin", "Operations"],
    "vw_ops_quality": ["Admin", "Operations"],
    "vw_ops_data_freshness": ["Admin", "Operations"],
    "vw_ops_sensor_inventory": ["Admin", "Operations"],
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
