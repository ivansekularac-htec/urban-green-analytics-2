from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SensorStatus
from app.models.mixins import TimestampMixin


class Sensor(Base, TimestampMixin):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id"),
        nullable=False,
    )

    serial_number: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    sensor_type_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_types.id"),
        nullable=False,
    )

    status: Mapped[SensorStatus] = mapped_column(
        SqlEnum(SensorStatus),
        nullable=False,
    )

    installed_at: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    sensor_type: Mapped["SensorType"] = relationship(back_populates="sensors")
