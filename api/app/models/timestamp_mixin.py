"""Reusable mixins for SQLAlchemy ORM models."""

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.models.utils import get_current_timestamp


class TimestampMixin:
    """Mixin adding created_at and updated_at timestamp columns."""

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=get_current_timestamp(),
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=get_current_timestamp(),
        onupdate=get_current_timestamp(),
    )
