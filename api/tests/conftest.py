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

os.environ.setdefault("OPERATIONS_EMAIL", "operations@example.com")
os.environ.setdefault("OPERATIONS_PASSWORD", "test-operations-password")
os.environ.setdefault("OPERATIONS_FULL_NAME", "Operations Team")
os.environ.setdefault("OPERATIONS_FARM_IDS", "[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]")

os.environ.setdefault("FARM_MANAGER_EMAIL", "manager@example.com")
os.environ.setdefault("FARM_MANAGER_PASSWORD", "test-manager-password")
os.environ.setdefault("FARM_MANAGER_FULL_NAME", "Farm Manager")
os.environ.setdefault("FARM_MANAGER_FARM_IDS", "[1]")
