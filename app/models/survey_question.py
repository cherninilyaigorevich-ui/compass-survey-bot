from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.survey import Survey
    from app.models.survey_response import SurveyResponse
    from app.models.survey_session import SurveySession


class SurveyQuestion(Base):
    """Вопрос внутри опроса."""

    __tablename__ = "survey_questions"

    __table_args__ = (
        UniqueConstraint(
            "survey_id",
            "code",
            name="uq_survey_questions_survey_code",
        ),
        UniqueConstraint(
            "survey_id",
            "position",
            name="uq_survey_questions_survey_position",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    survey_id: Mapped[int] = mapped_column(
        ForeignKey(
            "surveys.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answer_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    show_if_question_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "survey_questions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    show_if_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    survey: Mapped["Survey"] = relationship(
        back_populates="questions",
    )

    condition_question: Mapped["SurveyQuestion | None"] = relationship(
        remote_side="SurveyQuestion.id",
        foreign_keys=[show_if_question_id],
    )

    responses: Mapped[list["SurveyResponse"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )

    active_sessions: Mapped[list["SurveySession"]] = relationship(
        back_populates="current_question",
        foreign_keys="SurveySession.current_question_id",
    )
