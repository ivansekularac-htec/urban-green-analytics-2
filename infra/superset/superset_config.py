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
}

EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "id": "Urban Green",
        "label": "Urban Green",
        "description": "Urban Green Analytics palette",
        "isDefault": False,
        "colors": [
            "#1B5E20",
            "#2E7D32",
            "#388E3C",
            "#43A047",
            "#66BB6A",
            "#81C784",
            "#A5D6A7",
            "#C8E6C9",
        ],
    },
]

EXTRA_SEQUENTIAL_COLOR_SCHEMES = [
    {
        "id": "Urban Green Sequential",
        "label": "Urban Green Sequential",
        "colors": [
            "#E8F5E9",
            "#C8E6C9",
            "#A5D6A7",
            "#81C784",
            "#66BB6A",
            "#43A047",
            "#2E7D32",
            "#1B5E20",
        ],
    },
]
