"""
conftest.py
Shared pytest fixtures for API tests.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@compiles(BigInteger, "sqlite")
def compile_big_integer_sqlite(type_, compiler, **kw):
    """Compile BigInteger as Integer for SQLite autoincrement support."""
    return compiler.visit_INTEGER(Integer(), **kw)


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def remove_sqlite_schemas() -> None:
    """Remove PostgreSQL schema names so tables can be created in SQLite."""
    Base.metadata.schema = None

    for table in Base.metadata.tables.values():
        table.schema = None

        for foreign_key in table.foreign_keys:
            foreign_key._colspec = foreign_key._colspec.replace("app.", "")


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create an isolated SQLite database session for each test."""
    remove_sqlite_schemas()

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with the test database dependency."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
