from sqlalchemy import BigInteger, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.enums import SensorStatus
from app.database import Base
from app.helpers import get_current_timestamp


class Sensor(Base):
    """Model representing a sensor installed on a farm."""

    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )

    sensor_type_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_types.id"),
        nullable=False,
    )

    serial_number: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    status: Mapped[SensorStatus] = mapped_column(
        SqlEnum(SensorStatus, name="sensor_status"),
        nullable=False,
    )

    installed_at: Mapped[int | None] = mapped_column(
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
        back_populates="sensors",
    )

    sensor_type: Mapped["SensorType"] = relationship(
        back_populates="sensors",
    )