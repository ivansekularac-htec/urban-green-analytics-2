"""
conftest.py
Shared pytest fixtures for Urban Green Analytics API.

Uses in-memory SQLite for fast unit tests.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------
# Fix import path
# ---------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------
# Fake env (so Settings don't try Postgres)
# ---------------------------------------------------------------------
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "testdb")
os.environ.setdefault("POSTGRES_SCHEMA", "app")

# ---------------------------------------------------------------------
# App imports AFTER env setup
# ---------------------------------------------------------------------
import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------
# SQLite engine (in-memory)
# ---------------------------------------------------------------------
SQLITE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------------------
# IMPORTANT: SQLite compatibility fixes
# ---------------------------------------------------------------------

# 1. Remove schema prefix
Base.metadata.schema = None

for table in Base.metadata.tables.values():
    # remove schema like "app."
    table.schema = None

    # 2. Fix BigInteger PK auto-increment in SQLite
    for column in table.columns:
        if isinstance(column.type, BigInteger) and column.primary_key:
            column.type = Integer()


# ---------------------------------------------------------------------
# Dependency override
# ---------------------------------------------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
@pytest.fixture(autouse=True)
def setup_db():
    """
    Recreate all tables before each test.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    """
    FastAPI test client with DB override.
    """
    with patch("app.main.verify_database_connection"), TestClient(app) as c:
        yield c
