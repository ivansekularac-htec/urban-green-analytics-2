"""
farm_crop.py
SQLAlchemy ORM model for the farm_crops table.

This module defines the FarmCrop association entity used
to track crop cultivation periods on individual farms.
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TIMESTAMP_DEFAULT

if TYPE_CHECKING:
    from app.models.crop import Crop
    from app.models.farm import Farm


class FarmCrop(Base):
    """ORM model for the farm_crops table."""

    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    crop_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=TIMESTAMP_DEFAULT,
    )

    farm: Mapped["Farm"] = relationship(back_populates="farm_crops")
    crop: Mapped["Crop"] = relationship(back_populates="farm_crops")
