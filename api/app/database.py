"""
Database configuration module.

Handles PostgreSQL connection setup using SQLAlchemy, manages
database sessions, loads credentials from environment variables,
and verifies database connectivity on application startup.
"""

import logging
import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Validate required variables
required_vars = {
    "POSTGRES_HOST": POSTGRES_HOST,
    "POSTGRES_PORT": POSTGRES_PORT,
    "POSTGRES_USER": POSTGRES_USER,
    "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
    "POSTGRES_DB": POSTGRES_DB,
}

missing = [key for key, value in required_vars.items() if not value]

if missing:
    raise ValueError(f"Missing required database environment variables: {', '.join(missing)}")

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
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
