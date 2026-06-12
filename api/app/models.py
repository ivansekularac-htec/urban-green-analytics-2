import time
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    desc,
)
from sqlalchemy.orm import relationship

from app.database import Base


class FarmStatus(StrEnum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class SensorStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


def get_current_timestamp():
    return int(time.time())


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    user_roles = relationship("UserRole", back_populates="role")


class QualityGrade(Base):
    __tablename__ = "quality_grades"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    harvests = relationship("Harvest", back_populates="quality_grade")


class FarmInfrastructureType(Base):
    __tablename__ = "farm_infrastructure_types"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farms = relationship("Farm", back_populates="infrastructure_type")


class GrowingSystemType(Base):
    __tablename__ = "growing_system_types"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farms = relationship("Farm", back_populates="growing_system_type")


class CropCategory(Base):
    __tablename__ = "crop_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    crops = relationship("Crop", back_populates="category")


class SensorType(Base):
    __tablename__ = "sensor_types"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    unit = Column(String(50), nullable=False)
    description = Column(String(500))
    optimal_min = Column(Numeric(10, 3))
    optimal_max = Column(Numeric(10, 3))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    sensors = relationship("Sensor", back_populates="sensor_type")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    infrastructure_type_id = Column(
        BigInteger, ForeignKey("farm_infrastructure_types.id"), nullable=False
    )
    growing_system_type_id = Column(
        BigInteger, ForeignKey("growing_system_types.id"), nullable=False
    )
    name = Column(String(255), nullable=False)
    city = Column(String(255))
    size_m2 = Column(Numeric(10, 3))
    status = Column(
        Enum(FarmStatus, name="farm_status", create_type=False),
        nullable=False,
        default=FarmStatus.ACTIVE,
    )
    growing_beds_count = Column(Integer)
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    infrastructure_type = relationship("FarmInfrastructureType", back_populates="farms")
    growing_system_type = relationship("GrowingSystemType", back_populates="farms")
    sensors = relationship("Sensor", back_populates="farm")
    user_roles = relationship("UserRole", back_populates="farm")
    farm_crops = relationship("FarmCrop", back_populates="farm")
    harvests = relationship("Harvest", back_populates="farm")


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    user_roles = relationship("UserRole", back_populates="user")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, ForeignKey("crop_categories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    category = relationship("CropCategory", back_populates="crops")
    farm_crops = relationship("FarmCrop", back_populates="crop")
    harvests = relationship("Harvest", back_populates="crop")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"))
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    farm = relationship("Farm", back_populates="user_roles")

    __table_args__ = (UniqueConstraint("user_id", "role_id", "farm_id", name="uq_user_role_farm"),)


class FarmCrop(Base):
    __tablename__ = "farm_crops"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(BigInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(BigInteger, nullable=False)
    ended_at = Column(BigInteger)
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farm = relationship("Farm", back_populates="farm_crops")
    crop = relationship("Crop", back_populates="farm_crops")


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    sensor_type_id = Column(BigInteger, ForeignKey("sensor_types.id"), nullable=False)
    serial_number = Column(String(255), nullable=False, unique=True)
    status = Column(
        Enum(SensorStatus, name="sensor_status", create_type=False),
        nullable=False,
        default=SensorStatus.ACTIVE,
    )
    installed_at = Column(BigInteger)
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    sensor_type = relationship("SensorType", back_populates="sensors")
    farm = relationship("Farm", back_populates="sensors")


class Harvest(Base):
    __tablename__ = "harvests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id"), nullable=False)
    crop_id = Column(BigInteger, ForeignKey("crops.id"), nullable=False)
    quality_grade_id = Column(BigInteger, ForeignKey("quality_grades.id"), nullable=False)
    weight_kg = Column(Numeric(10, 3), nullable=False)
    created_at = Column(BigInteger, nullable=False, default=get_current_timestamp)
    updated_at = Column(
        BigInteger, nullable=False, default=get_current_timestamp, onupdate=get_current_timestamp
    )
    farm = relationship("Farm", back_populates="harvests")
    crop = relationship("Crop", back_populates="harvests")
    quality_grade = relationship("QualityGrade", back_populates="harvests")
    __table_args__ = (Index("idx_harvests_farm", "farm_id", desc("updated_at")),)
