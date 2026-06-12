from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import SensorStatus


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id"),
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

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    installed_at: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    sensor_type: Mapped["SensorType"] = relationship(back_populates="sensors")
