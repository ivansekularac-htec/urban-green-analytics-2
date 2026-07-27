"""Runtime configuration for Apache Superset.

Runs Superset as a single-process service with in-memory caching and
without Celery, Redis, async SQL Lab, scheduled reports, or thumbnails.
"""

import os

# Session signing and encrypted metadata.
SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# Disable Celery and all background workers.
CELERY_CONFIG = None

# In-process cache (SimpleCache). No Redis or other external cache service.
_CACHE = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}
CACHE_CONFIG = _CACHE
DATA_CACHE_CONFIG = _CACHE

# Explicitly off so the UI does not offer async/thumbnail/alert features.
FEATURE_FLAGS = {
    "THUMBNAILS": False,
    "ALERT_REPORTS": False,
    "GLOBAL_ASYNC_QUERIES": False,
    "SQLLAB_FORCE_RUN_ASYNC": False,
    "PLAYWRIGHT_REPORTS_AND_THUMBNAILS": False,
    "ENABLE_DASHBOARD_SCREENSHOT_ENDPOINTS": False,
}

# Keep timestamps aligned with the rest of the platform.
BABEL_DEFAULT_TIMEZONE = "UTC"
