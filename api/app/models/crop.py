from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("crop_categories.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    category: Mapped["CropCategory"] = relationship(back_populates="crops")
    harvests: Mapped[list["Harvest"]] = relationship(back_populates="crop")
    farm_crops: Mapped[list["FarmCrop"]] = relationship(back_populates="crop")
