"""Pytest configuration.

Sets database environment variables before any application module is imported
so ``Settings()`` can be constructed without a real ``.env`` file. CI sets
these in the workflow; this is the local fallback.
"""

import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_SCHEMA", "app")
