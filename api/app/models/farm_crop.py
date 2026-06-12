from sqlalchemy import (
    BigInteger,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.mixins import TimestampMixin
from app.models.crop import Crop
from app.models.farm import Farm


class FarmCrop(TimestampMixin, Base):
    __tablename__ = "farm_crops"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("app.farms.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("app.crops.id", ondelete="CASCADE"), nullable=False
    )

    started_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    farm: Mapped["Farm"] = relationship(
        back_populates="farm_crops",
    )

    crop: Mapped["Crop"] = relationship(
        back_populates="farm_crops",
    )
