"""
conftest.py
Shared pytest fixtures for the Urban Green Analytics API test.

Sets up an in-memory SQLite database and a FastAPI TestClient that
uses that database instead of the real PostgreSQL instance.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Keep existing sys.path fix
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# SQLite in-memory engine
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# SQLite compatibility:
# 1. Strip PostgreSQL schema prefix from all tables
# 2. Replace BigInteger PKs with Integer so SQLite treats them as rowid
#    aliases and auto-increments them (BIGINT PRIMARY KEY does NOT
#    auto-increment in SQLite; only INTEGER PRIMARY KEY does)
Base.metadata.schema = None
for _table in Base.metadata.sorted_tables:
    _table.schema = None
    for _col in _table.columns:
        if isinstance(_col.type, BigInteger) and _col.primary_key:
            _col.type = Integer()

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

# ---------------------------------------------------------------------------
# Dependency override
# ---------------------------------------------------------------------------


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_db():
    """Recreate all tables before every test for full isolation."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def client():
    """
    Session-scoped TestClient.

    verify_database_connection() is patched so the lifespan startup
    does not attempt to reach the real PostgreSQL instance.
    """
    with patch("app.main.verify_database_connection"), TestClient(app) as c:
        yield c
