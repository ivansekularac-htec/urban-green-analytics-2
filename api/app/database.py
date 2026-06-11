"""
database.py

Database configuration and connection management.

This module creates the SQLAlchemy engine, session factory,
and verifies database connectivity.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.settings import settings


# Base class for all ORM models.
Base = declarative_base()


def get_database_url() -> str:
    """Build the PostgreSQL connection URL from application settings.

    Returns:
        str: Database connection URL.
    """

    return (
        f"postgresql://{settings.postgres_user}:"
        f"{settings.postgres_password}@"
        f"{settings.postgres_host}:"
        f"{settings.postgres_port}/"
        f"{settings.postgres_db}"
    )


def create_db_engine():
    """Create the SQLAlchemy database engine.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """

    return create_engine(get_database_url())


def verify_connection(engine) -> None:
    """Verify database connectivity using a test query.

    Args:
        engine: SQLAlchemy engine instance.

    Raises:
        Exception: If the connection fails.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("Database connection successful")

    except Exception as error:
        print(f"Database connection failed: {error}")
        raise


# SQLAlchemy engine instance.
engine = create_db_engine()

# Factory for creating database sessions.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Verify database connection on startup.
verify_connection(engine)