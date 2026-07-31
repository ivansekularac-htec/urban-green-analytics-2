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

os.environ.setdefault("DEMO_FARM_MANAGER_USERNAME", "fm1")
os.environ.setdefault("DEMO_FARM_MANAGER_FIRSTNAME", "Farm")
os.environ.setdefault("DEMO_FARM_MANAGER_LASTNAME", "Manager")
os.environ.setdefault("DEMO_FARM_MANAGER_EMAIL", "fm1@urbangreen.com")
os.environ.setdefault("DEMO_FARM_MANAGER_PASSWORD", "test-user-password")

os.environ.setdefault("DEMO_OPERATIONS_USERNAME", "ot1")
os.environ.setdefault("DEMO_OPERATIONS_FIRSTNAME", "Operations")
os.environ.setdefault("DEMO_OPERATIONS_LASTNAME", "Team")
os.environ.setdefault("DEMO_OPERATIONS_EMAIL", "ot1@urbangreen.com")
os.environ.setdefault("DEMO_OPERATIONS_PASSWORD", "test-user-password")
