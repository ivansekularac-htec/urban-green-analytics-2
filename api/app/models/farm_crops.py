from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.helpers import get_current_timestamp

class FarmCrop(Base):
    """Model representing a farm crop."""

    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )

    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
    )

    started_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    ended_at: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

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

    farm: Mapped["Farm"] = relationship(
        back_populates="farm_crops",
    )

    crop: Mapped["Crop"] = relationship(
        back_populates="farm_crops",
    )