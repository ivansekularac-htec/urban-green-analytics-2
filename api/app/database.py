"""
@File: database.py
Database configuration for the Urban Green Analytics API.

This module configures the SQLAlchemy engine, session factory, ORM base class,
database dependency, and startup connection verification for PostgreSQL.
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models"""

    pass


DATABASE_URL = (
    f"postgresql+psycopg2://{settings.postgres_user}:"
    f"{settings.postgres_password}@"
    f"{settings.postgres_host}:"
    f"{settings.postgres_port}"
    f"/{settings.postgres_db}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Create and provide a database session for a single request.

    This function is intended to be used as a FastAPI dependency.
    It creates a SQLAlchemy session before the request handler runs
    and closes it after the request has finished.

    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_database_connection() -> None:
    """Verify that the application can connect to the PostgreSQL database.

    Executes a lightweight ``SELECT 1`` query against the configured database.
    If the connection fails, the exception is logged and re-raised so the
    application startup can fail fast.

    Raises:
        SQLAlchemyError: If the database connection or query execution fails.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except SQLAlchemyError:
        logger.exception("Database connection failed")
        raise
