"""
InfrastructureType ORM model.

Represents cultivation methods used in farms, such as hydroponic or aeroponic
systems, defining how crops are grown without traditional soil-based farming.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.farms.farm import Farm


class InfrastructureType(Base, AuditMixin):
    __tablename__ = "farm_infrastructure_types"

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
        back_populates="infrastructure_type",
    )
