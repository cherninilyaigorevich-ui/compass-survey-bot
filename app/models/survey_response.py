from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.survey_question import SurveyQuestion
    from app.models.survey_session import SurveySession


class SurveyResponse(Base):
    """Ответ на конкретный вопрос в рамках одной сессии."""

    __tablename__ = "survey_responses"

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "question_id",
            name="uq_survey_responses_session_question",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "survey_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "survey_questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    session: Mapped["SurveySession"] = relationship(
        back_populates="responses",
    )

    question: Mapped["SurveyQuestion"] = relationship(
        back_populates="responses",
    )
