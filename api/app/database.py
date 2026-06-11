"""
Database configuration module.

Handles PostgreSQL connection setup using SQLAlchemy, manages
database sessionsand verifies database connectivity on application
startup.
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}"
    f"/{settings.postgres_db}"
)

# SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative Base
Base = declarative_base()


def verify_database_connection() -> None:
    """
    Verify PostgreSQL connectivity during application startup.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Successfully connected to PostgreSQL database.")
    except SQLAlchemyError as exc:
        logger.exception("Failed to connect to PostgreSQL database.")
        raise exc


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
