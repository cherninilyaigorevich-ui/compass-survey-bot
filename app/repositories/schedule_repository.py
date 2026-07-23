from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.survey_schedule import SurveySchedule


class ScheduleRepository:
    """Работа с расписаниями периодических опросов."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(
        self,
        *,
        user_id: int,
        survey_id: int,
    ) -> SurveySchedule | None:
        statement = select(SurveySchedule).where(
            SurveySchedule.user_id == user_id,
            SurveySchedule.survey_id == survey_id,
        )

        return self.db.scalar(statement)

    def get_or_create(
        self,
        *,
        user_id: int,
        survey_id: int,
        next_run_at: datetime | None = None,
    ) -> SurveySchedule:
        schedule = self.get(
            user_id=user_id,
            survey_id=survey_id,
        )

        if schedule is not None:
            return schedule

        schedule = SurveySchedule(
            user_id=user_id,
            survey_id=survey_id,
            enabled=True,
            next_run_at=next_run_at,
        )

        self.db.add(schedule)
        self.db.flush()

        return schedule

    def list_due(
        self,
        now: datetime,
    ) -> list[SurveySchedule]:
        statement = (
            select(SurveySchedule)
            .options(
                selectinload(SurveySchedule.user),
                selectinload(SurveySchedule.survey),
            )
            .where(
                SurveySchedule.enabled.is_(True),
                SurveySchedule.next_run_at.is_not(None),
                SurveySchedule.next_run_at <= now,
            )
            .order_by(SurveySchedule.next_run_at)
        )

        return list(self.db.scalars(statement).all())

    def mark_sent(
        self,
        *,
        schedule: SurveySchedule,
        sent_at: datetime,
        next_run_at: datetime,
    ) -> SurveySchedule:
        schedule.last_sent_at = sent_at
        schedule.next_run_at = next_run_at

        self.db.flush()

        return schedule

    def mark_completed(
        self,
        *,
        schedule: SurveySchedule,
        completed_at: datetime,
    ) -> SurveySchedule:
        schedule.last_completed_at = completed_at

        self.db.flush()

        return schedule
