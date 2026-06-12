from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.helpers import get_current_timestamp


class TimestampMixin:
    """Provides created_at and updated_at timestamp fields."""

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
        onupdate=get_current_timestamp,
    )
