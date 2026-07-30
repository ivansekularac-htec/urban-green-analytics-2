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

os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production-but-long-enough")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRES_MINUTES", "60")

os.environ.setdefault("SUPERUSER_EMAIL", "admin@example.com")
os.environ.setdefault("SUPERUSER_PASSWORD", "test-admin-password")
os.environ.setdefault("SUPERUSER_FULL_NAME", "Test Administrator")

os.environ.setdefault("DEMO_FARM_MANAGER_EMAIL", "manager1@urbangreen.com")
os.environ.setdefault("DEMO_FARM_MANAGER_PASSWORD", "urbangreen_password")
os.environ.setdefault("DEMO_FARM_MANAGER_FULL_NAME", "Test Farm Manager")
os.environ.setdefault("DEMO_FARM_MANAGER_FARM_ID", "1")

os.environ.setdefault("DEMO_OPS_EMAIL", "ops1@urbangreen.com")
os.environ.setdefault("DEMO_OPS_PASSWORD", "urbangreen_password")
os.environ.setdefault("DEMO_OPS_FULL_NAME", "Test Operations")
os.environ.setdefault("DEMO_OPS_FARM_IDS", "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15")
