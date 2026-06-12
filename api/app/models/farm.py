from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import FarmStatus


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    infrastructure_type_id: Mapped[int] = mapped_column(
        ForeignKey("farm_infrastructure_types.id"),
        nullable=False,
    )

    growing_system_type_id: Mapped[int] = mapped_column(
        ForeignKey("growing_system_types.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    city: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    size_m2: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    status: Mapped[FarmStatus] = mapped_column(
        SqlEnum(FarmStatus),
        nullable=False,
    )

    growing_beds_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    infrastructure_type: Mapped["FarmInfrastructureType"] = relationship(back_populates="farms")
    growing_system_type: Mapped["GrowingSystemType"] = relationship(back_populates="farms")
    harvests: Mapped[list["Harvest"]] = relationship(back_populates="farm")
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="farm")
    farm_crops: Mapped[list["FarmCrop"]] = relationship(back_populates="farm")
