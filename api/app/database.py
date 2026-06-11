"""
database.py

Database configuration and session management for the Urban Green Analytics API.

This module is responsible for configuring SQLAlchemy and providing
shared database resources used throughout the application.

The module defines:

- DATABASE_URL: Connection string used to connect to PostgreSQL.
- engine: SQLAlchemy engine responsible for managing database connections.
- SessionLocal: Factory used to create database sessions for application
  requests and background tasks.
- Base: Declarative base class that all ORM models inherit from.

These objects are intended to be imported and reused across the
application to ensure consistent database access and session handling.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# SQLAlchemy connection URL constructed from application settings.
DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{settings.postgres_user}:"
    f"{settings.postgres_password}@"
    f"{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

# SQLAlchemy engine responsible for managing database connections
# and connection pooling.
engine = create_engine(DATABASE_URL)

# Session factory used to create database sessions.
#
# A new session should typically be created for each request and
# closed when the request has been completed.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All database model classes should inherit from this class to gain
    SQLAlchemy's declarative mapping functionality and metadata
    registration.
    """

    pass
