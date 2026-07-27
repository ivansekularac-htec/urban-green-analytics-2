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


SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY")

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
    "SQLLAB_BACKEND_PERSISTENCE": False,
}

# Create connection
ch_user = os.getenv("CLICKHOUSE_USER", "urbangreen")
ch_pass = os.getenv("CLICKHOUSE_PASSWORD", "")
ch_host = os.getenv("CLICKHOUSE_HOST", "urbangreen-clickhouse")
ch_port = os.getenv("CLICKHOUSE_HTTP_PORT", "8123")
ch_db = os.getenv("CLICKHOUSE_DB", "urbangreen_dw")

# Build the dynamic connection string
CLICKHOUSE_CONNECTION_STRING = (
    f"clickhousedb://{ch_user}:{ch_pass}@{ch_host}:{ch_port}/{ch_db}"
)
