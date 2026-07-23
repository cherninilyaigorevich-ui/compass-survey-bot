from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.survey_schedule import SurveySchedule
    from app.models.survey_session import SurveySession


class CompassUser(Base):
    """
    Пользователь Compass, который взаимодействовал с ботом.

    compass_user_id — идентификатор пользователя, полученный
    во входящем webhook Compass.
    """

    __tablename__ = "compass_users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    compass_user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        index=True,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    last_group_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    last_message_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    current_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    schedules: Mapped[list["SurveySchedule"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    sessions: Mapped[list["SurveySession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
