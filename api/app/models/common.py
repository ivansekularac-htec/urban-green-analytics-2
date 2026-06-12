"""
common.py
Shared SQLAlchemy model utilities.

This module contains reusable constants and helpers shared
across ORM model definitions.
"""

from sqlalchemy import BigInteger, text
from sqlalchemy.orm import Mapped, mapped_column

TIMESTAMP_DEFAULT = text("EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT")


class TimestampMixin:
    """Mixin adding common timestamp columns to ORM models."""

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
        onupdate=TIMESTAMP_DEFAULT,
    )
