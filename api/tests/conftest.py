"""Pytest configuration.

Sets database environment variables before any application module is imported
so ``Settings()`` can be constructed without a real ``.env`` file. CI sets
these in the workflow; this is the local fallback.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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


@pytest.fixture
def db_session() -> MagicMock:
    """Return a SQLAlchemy-compatible mocked session for API tests."""
    return MagicMock(spec=Session)


@pytest.fixture
def client(db_session: MagicMock) -> TestClient:
    """Return a test client that never opens a live database connection."""
    from app.database import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with (
            patch("app.main.verify_database_connection"),
            patch("app.main.SessionLocal"),
            patch("app.main.ensure_superuser"),
            patch("app.main.ensure_demo_users"),
            TestClient(app) as test_client,
        ):
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
