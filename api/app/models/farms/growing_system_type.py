"""
GrowingSystemType ORM model.

Represents spatial farm production layouts, such as vertical farming,
tower systems, and flat-bed cultivation, defining how crops are physically
organized within a growing environment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.farms.farm import Farm


class GrowingSystemType(Base, AuditMixin):
    __tablename__ = "growing_system_types"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    farms: Mapped[list[Farm]] = relationship(
        back_populates="growing_system_type",
    )
