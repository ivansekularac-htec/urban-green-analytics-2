"""
mixins.py
Reusable mixins for ORM models.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, text
from sqlalchemy.orm import Mapped, mapped_column

from app.helpers import get_current_timestamp


class TimestampMixin:
    """Mixin for adding created_at and updated_at audit fields to models."""

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
        server_default=text("EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT"),
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
        server_default=text("EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT"),
        onupdate=get_current_timestamp,
    )
