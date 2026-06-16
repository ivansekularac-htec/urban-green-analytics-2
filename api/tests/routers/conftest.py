"""
Shared router test fixtures.
"""

import sqlite3
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import BigInteger, Integer, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app


@asynccontextmanager
async def test_lifespan(_app):
    """
    Disable production startup checks for router tests.

    Router tests use an isolated SQLite database through dependency overrides,
    so the production PostgreSQL connection check must not run here.
    """
    yield


app.router.lifespan_context = test_lifespan


def patch_sqlite_column_types():
    """
    Replace BigInteger columns with Integer for SQLite tests.

    SQLite autoincrement works only when the primary key column is exactly
    INTEGER PRIMARY KEY.
    """
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, BigInteger):
                column.type = Integer()


patch_sqlite_column_types()

SQLALCHEMY_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@event.listens_for(test_engine, "connect")
def configure_sqlite(dbapi_connection, _connection_record):
    """
    Configure SQLite connection for tests.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")

    try:
        cursor.execute("ATTACH DATABASE ':memory:' AS app")
    except sqlite3.OperationalError as exc:
        if "already in use" not in str(exc):
            raise

    cursor.close()


@pytest.fixture(autouse=True)
def reset_database():
    """
    Reset SQLite database before each router test.
    """
    with test_engine.begin() as connection:
        Base.metadata.drop_all(bind=connection)
        Base.metadata.create_all(bind=connection)

    yield


@pytest.fixture
def db_session():
    """
    Create a SQLite database session for tests.
    """
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """
    Create a FastAPI test client using the SQLite test database.
    """

    def override_get_db():
        db: Session = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
