"""
Custom configuration for the UrbanGreen Analytics Superset deployment.

This configuration intentionally keeps Superset as a single-process
application:
- SQLite metadata database stored in the persistent volume
- In-process cache
- No external services (Redis, Celery)
"""

import os

# Security


SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SUPERSET_SECRET_KEY environment variable must be set")


# Timezone


DEFAULT_TIMEZONE = "UTC"


# Cache


CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}


# Feature flags
#
# These are already False by default in Superset 5.0.0, but we set them
# explicitly to document that this deployment intentionally does not use
# asynchronous/background services.


FEATURE_FLAGS = {
    "ALERT_REPORTS": False,
    "THUMBNAILS": False,
    "THUMBNAILS_SQLA_LISTENERS": False,
    "ENABLE_DASHBOARD_SCREENSHOT_ENDPOINTS": False,
    "ENABLE_DASHBOARD_DOWNLOAD_WEBDRIVER_SCREENSHOT": False,
    "GLOBAL_ASYNC_QUERIES": False,
    "SQLLAB_ASYNC_TIME_LIMIT_SEC": 0,
    # Required for {{ current_username() }} in Row-Level Security clauses.
    # Trusted editors only (Admin); custom roles only view assigned dashboards.
    "ENABLE_TEMPLATE_PROCESSING": True,
    # Restrict dashboard visibility to roles assigned on each dashboard.
    "DASHBOARD_RBAC": True,
}
