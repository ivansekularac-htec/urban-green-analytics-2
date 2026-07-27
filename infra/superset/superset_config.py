import os

# Session signing key.
SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# Disable Celery and background workers.
CELERY_CONFIG = None

# In-process cache.
_CACHE = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}
CACHE_CONFIG = _CACHE
DATA_CACHE_CONFIG = _CACHE

# Disable asynchronous/background features.
FEATURE_FLAGS = {
    "THUMBNAILS": False,
    "ALERT_REPORTS": False,
    "GLOBAL_ASYNC_QUERIES": False,
    "SQLLAB_FORCE_RUN_ASYNC": False,
    "PLAYWRIGHT_REPORTS_AND_THUMBNAILS": False,
    "ENABLE_DASHBOARD_SCREENSHOT_ENDPOINTS": False,
}

# Do not load example dashboards.
SUPERSET_LOAD_EXAMPLES = False

# Keep timestamps in UTC.
BABEL_DEFAULT_TIMEZONE = "UTC"
