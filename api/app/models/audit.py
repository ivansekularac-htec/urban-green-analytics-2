"""
Audit mixin that adds creation and update timestamp fields to ORM models.
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column


def epoch_now() -> int:
    return int(datetime.now(UTC).timestamp())


class AuditMixin:
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        default=epoch_now,
        nullable=False,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        default=epoch_now,
        onupdate=epoch_now,
        nullable=False,
    )
