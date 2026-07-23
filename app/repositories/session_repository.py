from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.survey_question import SurveyQuestion
from app.models.survey_response import SurveyResponse
from app.models.survey_session import SurveySession


class SessionRepository:
    """Работа с сессиями прохождения опросов и ответами."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self,
        session_id: int,
    ) -> SurveySession | None:
        statement = (
            select(SurveySession)
            .options(
                selectinload(SurveySession.responses),
                selectinload(SurveySession.current_question),
            )
            .where(SurveySession.id == session_id)
        )

        return self.db.scalar(statement)

    def get_active_for_user(
        self,
        user_id: int,
    ) -> SurveySession | None:
        statement = (
            select(SurveySession)
            .options(
                selectinload(SurveySession.responses),
                selectinload(SurveySession.current_question),
                selectinload(SurveySession.survey),
            )
            .where(
                SurveySession.user_id == user_id,
                SurveySession.status == "active",
            )
            .order_by(SurveySession.started_at.desc())
            .limit(1)
        )

        return self.db.scalar(statement)

    def get_active_for_user_and_survey(
        self,
        *,
        user_id: int,
        survey_id: int,
    ) -> SurveySession | None:
        statement = (
            select(SurveySession)
            .options(
                selectinload(SurveySession.responses),
                selectinload(SurveySession.current_question),
            )
            .where(
                SurveySession.user_id == user_id,
                SurveySession.survey_id == survey_id,
                SurveySession.status == "active",
            )
            .order_by(SurveySession.started_at.desc())
            .limit(1)
        )

        return self.db.scalar(statement)

    def create(
        self,
        *,
        user_id: int,
        survey_id: int,
        current_question_id: int | None,
    ) -> SurveySession:
        session = SurveySession(
            user_id=user_id,
            survey_id=survey_id,
            current_question_id=current_question_id,
            status="active",
            started_at=datetime.now(timezone.utc),
        )

        self.db.add(session)
        self.db.flush()

        return session

    def set_current_question(
        self,
        *,
        session: SurveySession,
        question: SurveyQuestion | None,
    ) -> SurveySession:
        session.current_question_id = (
            question.id if question is not None else None
        )

        self.db.flush()

        return session

    def get_response(
        self,
        *,
        session_id: int,
        question_id: int,
    ) -> SurveyResponse | None:
        statement = select(SurveyResponse).where(
            SurveyResponse.session_id == session_id,
            SurveyResponse.question_id == question_id,
        )

        return self.db.scalar(statement)

    def save_response(
        self,
        *,
        session_id: int,
        question_id: int,
        value: str,
    ) -> SurveyResponse:
        response = self.get_response(
            session_id=session_id,
            question_id=question_id,
        )

        if response is None:
            response = SurveyResponse(
                session_id=session_id,
                question_id=question_id,
                value=value,
                created_at=datetime.now(timezone.utc),
            )

            self.db.add(response)
        else:
            response.value = value
            response.created_at = datetime.now(timezone.utc)

        self.db.flush()

        return response

    def get_responses_map(
        self,
        session_id: int,
    ) -> dict[int, str]:
        statement = select(SurveyResponse).where(
            SurveyResponse.session_id == session_id,
        )

        responses = self.db.scalars(statement).all()

        return {
            response.question_id: response.value
            for response in responses
        }

    def complete(
        self,
        session: SurveySession,
    ) -> SurveySession:
        session.status = "completed"
        session.current_question_id = None
        session.completed_at = datetime.now(timezone.utc)
        session.cancelled_at = None

        self.db.flush()

        return session

    def cancel(
        self,
        session: SurveySession,
    ) -> SurveySession:
        session.status = "cancelled"
        session.current_question_id = None
        session.cancelled_at = datetime.now(timezone.utc)

        self.db.flush()

        return session
