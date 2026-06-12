"""
Audit mixin that adds creation and update timestamp fields to ORM models.
"""

from sqlalchemy import BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        server_default=func.extract("epoch", func.now()),
        nullable=False,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        server_default=func.extract("epoch", func.now()),
        onupdate=func.extract("epoch", func.now()),
        nullable=False,
    )
