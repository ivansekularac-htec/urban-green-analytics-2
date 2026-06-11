"""
database.py
Database configuration and session management for the Urban Green Analytics API.

This module configures the SQLAlchemy engine, session factory, and base
class used throughout the application. It also provides utilities for
database session management and connection verification.
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"options": f"-csearch_path={settings.postgres_schema}"},
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Provide a database session.

    This dependency creates a new SQLAlchemy session for each request
    and ensures that the session is closed after use.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def verify_database_connection() -> None:
    """Verify database connectivity.

    This function executes a simple query against the PostgreSQL database
    during application startup to confirm that the connection is working.

    Raises:
        RuntimeError: If the database connection check fails.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Database connection successful.")

    except SQLAlchemyError:
        logger.exception("Database connection failed.")
        raise
