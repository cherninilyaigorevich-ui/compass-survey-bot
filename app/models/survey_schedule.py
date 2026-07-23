from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.compass_user import CompassUser
    from app.models.survey import Survey


class SurveySchedule(Base):
    """
    Расписание опроса для конкретного пользователя.

    next_run_at определяет, когда бот должен отправить
    пользователю следующий опрос.
    """

    __tablename__ = "survey_schedules"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "survey_id",
            name="uq_survey_schedules_user_survey",
        ),
    )

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

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["CompassUser"] = relationship(
        back_populates="schedules",
    )

    survey: Mapped["Survey"] = relationship(
        back_populates="schedules",
    )
