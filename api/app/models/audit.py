"""
Audit mixin that adds creation and update timestamp fields to ORM models.
"""

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
