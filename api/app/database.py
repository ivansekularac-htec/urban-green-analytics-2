"""
database.py

Database configuration and connection management.

This module creates the SQLAlchemy engine, session factory,
and verifies database connectivity.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.settings import settings
import logging

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def verify_connection(engine) -> None:
    """Verify database connectivity using a test query.

    Args:
        engine: SQLAlchemy engine instance.

    Raises:
        SQLAlchemyError: If the connection fails.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Database connection successful")

    except SQLAlchemyError:
        logger.exception("Database connection failed")
        raise
        


# SQLAlchemy engine instance.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

# Factory for creating database sessions.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db() -> Iterator[Session]:
    """Yield a database session for a single request."""
    with SessionLocal() as session:
        yield session