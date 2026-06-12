from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    desc,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.helpers import get_current_timestamp


class FarmStatus(StrEnum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class SensorStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")


class QualityGrade(Base):
    __tablename__ = "quality_grades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(
        String(100),
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    harvests: Mapped[list["Harvest"]] = relationship("Harvest", back_populates="quality_grade")


class FarmInfrastructureType(Base):
    __tablename__ = "farm_infrastructure_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(
        String(500),
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farms: Mapped[list["Farm"]] = relationship("Farm", back_populates="infrastructure_type")


class GrowingSystemType(Base):
    __tablename__ = "growing_system_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(
        String(500),
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farms: Mapped[list["Farm"]] = relationship("Farm", back_populates="growing_system_type")


class CropCategory(Base):
    __tablename__ = "crop_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(
        String(500),
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    crops: Mapped[list["Crop"]] = relationship("Crop", back_populates="category")


class SensorType(Base):
    __tablename__ = "sensor_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    unit: Mapped[str] = mapped_column(
        String(50),
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
    )
    optimal_min: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
    )
    optimal_max: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    sensors: Mapped[list["Sensor"]] = relationship("Sensor", back_populates="sensor_type")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    infrastructure_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("farm_infrastructure_types.id"),
        nullable=False,
    )
    growing_system_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("growing_system_types.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
    )
    city: Mapped[str | None] = mapped_column(
        String(255),
    )
    size_m2: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
    )
    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus, name="farm_status"),
        default=FarmStatus.ACTIVE,
    )
    growing_beds_count: Mapped[int | None] = mapped_column(
        Integer,
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    infrastructure_type: Mapped["FarmInfrastructureType"] = relationship(
        "FarmInfrastructureType", back_populates="farms"
    )
    growing_system_type: Mapped["GrowingSystemType"] = relationship(
        "GrowingSystemType", back_populates="farms"
    )
    sensors: Mapped[list["Sensor"]] = relationship("Sensor", back_populates="farm")
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="farm")
    farm_crops: Mapped[list["FarmCrop"]] = relationship("FarmCrop", back_populates="farm")
    harvests: Mapped[list["Harvest"]] = relationship("Harvest", back_populates="farm")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(
        String(255),
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user")


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("crop_categories.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    category: Mapped["CropCategory"] = relationship("CropCategory", back_populates="crops")
    farm_crops: Mapped[list["FarmCrop"]] = relationship("FarmCrop", back_populates="crop")
    harvests: Mapped[list["Harvest"]] = relationship("Harvest", back_populates="crop")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id"),
        nullable=False,
    )

    farm_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=True,
    )

    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )

    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    farm: Mapped["Farm" | None] = relationship("Farm", back_populates="user_roles")

    __table_args__ = (UniqueConstraint("user_id", "role_id", "farm_id", name="uq_user_role_farm"),)


class FarmCrop(Base):
    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[int] = mapped_column(
        BigInteger,
    )
    ended_at: Mapped[int | None] = mapped_column(
        BigInteger,
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farm: Mapped["Farm"] = relationship("Farm", back_populates="farm_crops")
    crop: Mapped["Crop"] = relationship("Crop", back_populates="farm_crops")


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False
    )
    sensor_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sensor_types.id"), nullable=False
    )
    serial_number: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[SensorStatus] = mapped_column(
        Enum(SensorStatus, name="sensor_status"),
        default=SensorStatus.ACTIVE,
    )
    installed_at: Mapped[int | None] = mapped_column(
        BigInteger,
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    sensor_type: Mapped["SensorType"] = relationship("SensorType", back_populates="sensors")
    farm: Mapped["Farm"] = relationship("Farm", back_populates="sensors")


class Harvest(Base):
    __tablename__ = "harvests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("farms.id"), nullable=False)
    crop_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("crops.id"), nullable=False)
    quality_grade_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("quality_grades.id"), nullable=False
    )
    weight_kg: Mapped[float] = mapped_column(
        Numeric(10, 3),
    )
    created_at: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(
        BigInteger, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farm: Mapped["Farm"] = relationship("Farm", back_populates="harvests")
    crop: Mapped["Crop"] = relationship("Crop", back_populates="harvests")
    quality_grade: Mapped["QualityGrade"] = relationship("QualityGrade", back_populates="harvests")
    __table_args__ = (Index("idx_harvests_farm", "farm_id", desc("updated_at")),)
