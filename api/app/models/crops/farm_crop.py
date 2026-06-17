"""
FarmCrop ORM model.

Represents the cultivation history of a crop on a farm,
tracking when a crop was planted and optionally when it ended.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.crops.crop import Crop
    from app.models.farms.farm import Farm


class FarmCrop(Base, AuditMixin):
    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
    )

    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="CASCADE"),
    )

    started_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    ended_at: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    farm: Mapped[Farm] = relationship(
        back_populates="farm_crops",
    )

    crop: Mapped[Crop] = relationship(
        back_populates="farm_crops",
    )
