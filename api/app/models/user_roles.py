from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.helpers import get_current_timestamp

class UserRole(Base):
    """Association table for users and roles, with an optional farm association."""

    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "farm_id",
            name="uq_user_role_farm",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False,
    )

    farm_id: Mapped[int | None] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
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

    user: Mapped["User"] = relationship(
        back_populates="user_roles",
    )

    role: Mapped["Role"] = relationship(
        back_populates="user_roles",
    )

    farm: Mapped["Farm | None"] = relationship(
        back_populates="user_roles",
    )