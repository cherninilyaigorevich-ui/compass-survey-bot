from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.compass_user import CompassUser
from app.models.survey_question import SurveyQuestion
from app.models.survey_session import SurveySession
from app.repositories import (
    SessionRepository,
    SurveyRepository,
    UserRepository,
)
from app.services.answer_normalizer import (
    AnswerValidationError,
    normalize_answer,
)


class SurveyServiceError(RuntimeError):
    """Базовая ошибка сервиса опросов."""


class SurveyNotFoundError(SurveyServiceError):
    """Опрос не найден или отключён."""


class ActiveSurveyNotFoundError(SurveyServiceError):
    """У пользователя нет активного опроса."""


@dataclass(slots=True)
class SurveyResult:
    """
    Результат обработки действия с опросом.

    message — текст, который нужно отправить пользователю;
    completed — завершён ли опрос;
    session_id — идентификатор сессии;
    question_code — код текущего или следующего вопроса.
    """

    message: str
    completed: bool
    session_id: int
    question_code: str | None = None


class SurveyService:
    """Бизнес-логика запуска и прохождения опросов."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.surveys = SurveyRepository(db)
        self.sessions = SessionRepository(db)

    def register_user(
        self,
        *,
        compass_user_id: int,
        display_name: str | None = None,
        group_id: str | None = None,
        message_type: str | None = None,
    ) -> CompassUser:
        """
        Создаёт пользователя или обновляет сведения,
        полученные из последнего webhook.
        """

        return self.users.get_or_create(
            compass_user_id=compass_user_id,
            display_name=display_name,
            group_id=group_id,
            message_type=message_type,
        )

    def get_active_session(
        self,
        *,
        compass_user_id: int,
    ) -> SurveySession | None:
        user = self.users.get_by_compass_user_id(
            compass_user_id
        )

        if user is None:
            return None

        return self.sessions.get_active_for_user(user.id)

    def start_survey(
        self,
        *,
        compass_user_id: int,
        survey_code: str,
        display_name: str | None = None,
        group_id: str | None = None,
        message_type: str | None = None,
    ) -> SurveyResult:
        """
        Запускает опрос для пользователя.

        Если уже существует активная сессия, возвращает
        текущий вопрос без создания новой сессии.
        """

        user = self.register_user(
            compass_user_id=compass_user_id,
            display_name=display_name,
            group_id=group_id,
            message_type=message_type,
        )

        existing_session = self.sessions.get_active_for_user(
            user.id
        )

        if existing_session is not None:
            question = existing_session.current_question

            if question is None:
                self.sessions.complete(existing_session)

                return SurveyResult(
                    message=existing_session.survey.completion_message,
                    completed=True,
                    session_id=existing_session.id,
                )

            return SurveyResult(
                message=self._format_question(question),
                completed=False,
                session_id=existing_session.id,
                question_code=question.code,
            )

        survey = self.surveys.get_by_code(
            survey_code,
            enabled_only=True,
        )

        if survey is None:
            raise SurveyNotFoundError(
                f"Опрос {survey_code!r} не найден или отключён."
            )

        questions = self.surveys.get_questions(survey.id)

        first_question = self._find_next_question(
            questions=questions,
            current_position=0,
            responses={},
        )

        session = self.sessions.create(
            user_id=user.id,
            survey_id=survey.id,
            current_question_id=(
                first_question.id
                if first_question is not None
                else None
            ),
        )

        if first_question is None:
            self.sessions.complete(session)

            return SurveyResult(
                message=survey.completion_message,
                completed=True,
                session_id=session.id,
            )

        return SurveyResult(
            message=self._format_question(first_question),
            completed=False,
            session_id=session.id,
            question_code=first_question.code,
        )

    def process_answer(
        self,
        *,
        compass_user_id: int,
        raw_answer: str,
        display_name: str | None = None,
        group_id: str | None = None,
        message_type: str | None = None,
    ) -> SurveyResult:
        """
        Сохраняет ответ и возвращает следующий вопрос
        либо сообщение о завершении опроса.
        """

        user = self.register_user(
            compass_user_id=compass_user_id,
            display_name=display_name,
            group_id=group_id,
            message_type=message_type,
        )

        session = self.sessions.get_active_for_user(user.id)

        if session is None:
            raise ActiveSurveyNotFoundError(
                "У пользователя нет активного опроса."
            )

        current_question = session.current_question

        if current_question is None:
            self.sessions.complete(session)

            return SurveyResult(
                message=session.survey.completion_message,
                completed=True,
                session_id=session.id,
            )

        max_length = (
            255
            if current_question.code == "new_location"
            else None
        )

        normalized_answer = normalize_answer(
            answer_type=current_question.answer_type,
            value=raw_answer,
            max_length=max_length,
        )

        self.sessions.save_response(
            session_id=session.id,
            question_id=current_question.id,
            value=normalized_answer,
        )

        if current_question.code == "new_location":
            self.users.update_location(
                user=user,
                location=normalized_answer,
            )

        responses = self.sessions.get_responses_map(
            session.id
        )

        questions = self.surveys.get_questions(
            session.survey_id
        )

        next_question = self._find_next_question(
            questions=questions,
            current_position=current_question.position,
            responses=responses,
        )

        if next_question is None:
            self.sessions.complete(session)

            return SurveyResult(
                message=session.survey.completion_message,
                completed=True,
                session_id=session.id,
            )

        self.sessions.set_current_question(
            session=session,
            question=next_question,
        )

        return SurveyResult(
            message=self._format_question(next_question),
            completed=False,
            session_id=session.id,
            question_code=next_question.code,
        )

    def cancel_active_survey(
        self,
        *,
        compass_user_id: int,
    ) -> bool:
        """Отменяет активный опрос пользователя."""

        user = self.users.get_by_compass_user_id(
            compass_user_id
        )

        if user is None:
            return False

        session = self.sessions.get_active_for_user(user.id)

        if session is None:
            return False

        self.sessions.cancel(session)

        return True

    @staticmethod
    def _find_next_question(
        *,
        questions: list[SurveyQuestion],
        current_position: int,
        responses: dict[int, str],
    ) -> SurveyQuestion | None:
        """
        Находит следующий доступный вопрос.

        Условный вопрос показывается только тогда, когда
        ответ на связанный вопрос совпадает с show_if_value.
        """

        for question in questions:
            if question.position <= current_position:
                continue

            if question.show_if_question_id is None:
                return question

            actual_value = responses.get(
                question.show_if_question_id
            )

            if actual_value == question.show_if_value:
                return question

        return None

    @staticmethod
    def _format_question(
        question: SurveyQuestion,
    ) -> str:
        if question.answer_type == "yes_no":
            return (
                f"{question.text}\n\n"
                "Ответьте: Да или Нет."
            )

        return question.text


__all__ = [
    "ActiveSurveyNotFoundError",
    "AnswerValidationError",
    "SurveyNotFoundError",
    "SurveyResult",
    "SurveyService",
    "SurveyServiceError",
]
