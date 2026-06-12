from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

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
    description: Mapped[str | None] = mapped_column(String(500))


class QualityGrade(TimestampMixin, Base):
    __tablename__ = "quality_grades"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))


class FarmInfrastructureType(TimestampMixin, Base):
    __tablename__ = "farm_infrastructure_types"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500))


class GrowingSystemType(TimestampMixin, Base):
    __tablename__ = "growing_system_types"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500))


class CropCategory(TimestampMixin, Base):
    __tablename__ = "crop_categories"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500))


class SensorType(TimestampMixin, Base):
    __tablename__ = "sensor_types"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    optimal_min = mapped_column(Numeric(10, 3))
    optimal_max = mapped_column(Numeric(10, 3))


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

    size_m2 = mapped_column(Numeric(10, 3))

    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus, name="farm_status"),
        nullable=False,
        default=FarmStatus.ACTIVE,
    )

    growing_beds_count: Mapped[int | None] = mapped_column(Integer)


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


class Crop(TimestampMixin, Base):
    __tablename__ = "crops"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    category_id: Mapped[int] = mapped_column(ForeignKey("app.crop_categories.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))


"""
Join Tables
"""


class UserRole(TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("app.users.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("app.roles.id"), nullable=False)
    farm_id: Mapped[int | None] = mapped_column(ForeignKey("app.farms.id"))


class FarmCrop(TimestampMixin, Base):
    __tablename__ = "farm_crops"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(ForeignKey("app.farms.id"), nullable=False)
    crop_id: Mapped[int] = mapped_column(ForeignKey("app.crops.id"), nullable=False)

    started_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_at: Mapped[int | None] = mapped_column(BigInteger)


class Sensor(TimestampMixin, Base):
    __tablename__ = "sensors"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(ForeignKey("app.farms.id"), nullable=False)
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

    installed_at: Mapped[int | None] = mapped_column(BigInteger)


class Harvest(TimestampMixin, Base):
    __tablename__ = "harvests"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(ForeignKey("app.farms.id"), nullable=False)
    crop_id: Mapped[int] = mapped_column(ForeignKey("app.srops.id"), nullable=False)
    quality_grade_id: Mapped[int] = mapped_column(
        ForeignKey("app.quality_grades.id"), nullable=False
    )

    weight_kg = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )
