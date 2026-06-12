from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import FarmStatus, SensorStatus
from app.mixins import TimestampMixin

"""
Lookup Tables
"""


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="role",
    )


class QualityGrade(TimestampMixin, Base):
    __tablename__ = "quality_grades"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="quality_grade",
    )


class FarmInfrastructureType(TimestampMixin, Base):
    __tablename__ = "farm_infrastructure_types"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="infrastructure_type",
    )


class GrowingSystemType(TimestampMixin, Base):
    __tablename__ = "growing_system_types"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="growing_system_type",
    )


class CropCategory(TimestampMixin, Base):
    __tablename__ = "crop_categories"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    crops: Mapped[list["Crop"]] = relationship(
        back_populates="category",
    )


class SensorType(TimestampMixin, Base):
    __tablename__ = "sensor_types"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    optimal_min: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    optimal_max: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    sensors: Mapped[list["Sensor"]] = relationship(
        back_populates="sensor_type",
    )


"""
Main Tables
"""


class Farm(TimestampMixin, Base):
    __tablename__ = "farms"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    infrastructure_type_id: Mapped[int] = mapped_column(
        ForeignKey("app.farm_infrastructure_types.id"), nullable=False
    )
    growing_system_type_id: Mapped[int] = mapped_column(
        ForeignKey("app.growing_system_types.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str | None] = mapped_column(String(255))

    size_m2: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus, name="farm_status"),
        nullable=False,
        default=FarmStatus.ACTIVE,
    )

    growing_beds_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sensors: Mapped[list["Sensor"]] = relationship(
        back_populates="farm",
    )

    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="farm",
    )

    infrastructure_type: Mapped["FarmInfrastructureType"] = relationship(
        back_populates="farms",
    )

    growing_system_type: Mapped["GrowingSystemType"] = relationship(
        back_populates="farms",
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="farm",
    )

    farm_crops: Mapped[list["FarmCrop"]] = relationship(
        back_populates="farm",
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user",
    )


class Crop(TimestampMixin, Base):
    __tablename__ = "crops"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    category_id: Mapped[int] = mapped_column(ForeignKey("app.crop_categories.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category: Mapped["CropCategory"] = relationship(
        back_populates="crops",
    )

    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="crop",
    )

    farm_crops: Mapped[list["FarmCrop"]] = relationship(
        back_populates="crop",
    )


class Sensor(TimestampMixin, Base):
    __tablename__ = "sensors"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("app.farms.id", ondelete="CASCADE"), nullable=False
    )
    sensor_type_id: Mapped[int] = mapped_column(ForeignKey("app.sensor_types.id"), nullable=False)

    serial_number: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    status: Mapped[SensorStatus] = mapped_column(
        Enum(SensorStatus, name="sensor_status"),
        nullable=False,
        default=SensorStatus.ACTIVE,
    )

    installed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    farm: Mapped["Farm"] = relationship(
        back_populates="sensors",
    )

    sensor_type: Mapped["SensorType"] = relationship(
        back_populates="sensors",
    )


class Harvest(TimestampMixin, Base):
    __tablename__ = "harvests"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(ForeignKey("app.farms.id"), nullable=False)
    crop_id: Mapped[int] = mapped_column(ForeignKey("app.crops.id"), nullable=False)
    quality_grade_id: Mapped[int] = mapped_column(
        ForeignKey("app.quality_grades.id"), nullable=False
    )

    weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    farm: Mapped["Farm"] = relationship(
        back_populates="harvests",
    )

    crop: Mapped["Crop"] = relationship(
        back_populates="harvests",
    )

    quality_grade: Mapped["QualityGrade"] = relationship(
        back_populates="harvests",
    )


"""
Many-to-Many Tables
"""


class UserRole(TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "farm_id",
            name="uq_user_role_farm",
        ),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("app.users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("app.roles.id"), nullable=False)
    farm_id: Mapped[int | None] = mapped_column(
        ForeignKey("app.farms.id", ondelete="CASCADE"), nullable=True
    )

    user: Mapped["User"] = relationship(
        back_populates="user_roles",
    )

    role: Mapped["Role"] = relationship(
        back_populates="user_roles",
    )

    farm: Mapped["Farm"] = relationship(
        back_populates="user_roles",
    )


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
