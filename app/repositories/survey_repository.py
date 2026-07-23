from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.survey import Survey
from app.models.survey_question import SurveyQuestion


class SurveyRepository:
    """Работа с определениями опросов и вопросами."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, survey_id: int) -> Survey | None:
        statement = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.id == survey_id)
        )

        return self.db.scalar(statement)

    def get_by_code(
        self,
        code: str,
        *,
        enabled_only: bool = False,
    ) -> Survey | None:
        statement = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.code == code)
        )

        if enabled_only:
            statement = statement.where(Survey.enabled.is_(True))

        return self.db.scalar(statement)

    def list_enabled(self) -> list[Survey]:
        statement = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.enabled.is_(True))
            .order_by(Survey.id)
        )

        return list(self.db.scalars(statement).all())

    def get_question_by_id(
        self,
        question_id: int,
    ) -> SurveyQuestion | None:
        return self.db.get(SurveyQuestion, question_id)

    def get_questions(
        self,
        survey_id: int,
    ) -> list[SurveyQuestion]:
        statement = (
            select(SurveyQuestion)
            .where(SurveyQuestion.survey_id == survey_id)
            .order_by(SurveyQuestion.position)
        )

        return list(self.db.scalars(statement).all())

    def get_first_question(
        self,
        survey_id: int,
    ) -> SurveyQuestion | None:
        statement = (
            select(SurveyQuestion)
            .where(SurveyQuestion.survey_id == survey_id)
            .order_by(SurveyQuestion.position)
            .limit(1)
        )

        return self.db.scalar(statement)
