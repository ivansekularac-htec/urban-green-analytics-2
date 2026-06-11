"""
database.py
Database configuration and session management for the Urban Green Analytics API.

This module configures the SQLAlchemy engine, session factory, and base
class used throughout the application. It also provides utilities for
database session management and connection verification.
"""

import logging
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{settings.postgres_user}:"
    f"{settings.postgres_password}@"
    f"{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

engine = create_engine(
    DATABASE_URL, pool_pre_ping=True, connect_args={"options": "-csearch_path=app"}
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

    except Exception as e:
        logger.exception("Database connection failed.")
        raise RuntimeError(f"Database connection failed: {e}") from e
