"""
database.py

Database configuration and connection management.

This module creates the SQLAlchemy engine, session factory,
and verifies database connectivity.
"""

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

load_dotenv()

# Base class for all ORM models.
Base = declarative_base()


def get_database_url() -> str:
    """Build the PostgreSQL connection URL from environment variables.

    Returns:
        str: Database connection URL.

    Raises:
        ValueError: If required environment variables are missing.
    """

    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")

    required_vars = {
        "POSTGRES_USER": postgres_user,
        "POSTGRES_DB": postgres_db,
        "POSTGRES_PORT": postgres_port,
    }

    # Check for missing required environment variables.
    missing_vars = [key for key, value in required_vars.items() if not value]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return (
        f"postgresql://{postgres_user}:{postgres_password}"
        f"@{postgres_host}:{postgres_port}/{postgres_db}"
    )


def create_db_engine():
    """Create the SQLAlchemy database engine.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """

    database_url = get_database_url()
    return create_engine(database_url)


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

verify_connection(engine)