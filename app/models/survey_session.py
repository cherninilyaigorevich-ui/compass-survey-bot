from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.compass_user import CompassUser
    from app.models.survey import Survey
    from app.models.survey_question import SurveyQuestion
    from app.models.survey_response import SurveyResponse


class SurveySession(Base):
    """Конкретное прохождение опроса пользователем."""

    __tablename__ = "survey_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "compass_users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    survey_id: Mapped[int] = mapped_column(
        ForeignKey(
            "surveys.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    current_question_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "survey_questions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["CompassUser"] = relationship(
        back_populates="sessions",
    )

    survey: Mapped["Survey"] = relationship(
        back_populates="sessions",
    )

    current_question: Mapped["SurveyQuestion | None"] = relationship(
        back_populates="active_sessions",
        foreign_keys=[current_question_id],
    )

    responses: Mapped[list["SurveyResponse"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SurveyResponse.created_at",
    )
