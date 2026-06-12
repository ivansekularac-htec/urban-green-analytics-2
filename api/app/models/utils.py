"""
Utility helpers for SQLAlchemy ORM model definitions.
"""

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause


def get_current_timestamp() -> TextClause:
    """Return a PostgreSQL expression for the current Unix timestamp in seconds."""

    return text("EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT")
