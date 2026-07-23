from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.survey_question import SurveyQuestion
    from app.models.survey_schedule import SurveySchedule
    from app.models.survey_session import SurveySession


class Survey(Base):
    """Описание опроса."""

    __tablename__ = "surveys"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    completion_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Спасибо! Ваш ответ сохранён ✅",
    )

    interval_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=90,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    questions: Mapped[list["SurveyQuestion"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="SurveyQuestion.position",
    )

    schedules: Mapped[list["SurveySchedule"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
    )

    sessions: Mapped[list["SurveySession"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
    )
