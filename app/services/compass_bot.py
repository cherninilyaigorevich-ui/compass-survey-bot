import logging

from sqlalchemy.orm import Session

from app.services.answer_normalizer import AnswerValidationError
from app.services.survey_service import (
    ActiveSurveyNotFoundError,
    SurveyNotFoundError,
    SurveyService,
)

logger = logging.getLogger(__name__)


class CompassBotService:
    """
    Основной обработчик сообщений Compass.

    Поддерживает:
    - служебные команды;
    - запуск и отмену опроса;
    - ответы /да и /нет без учёта регистра;
    - указание локации командой /location;
    - подсказки при неправильных командах.
    """

    LOCATION_SURVEY_CODE = "location_check"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.survey_service = SurveyService(db)

    def process_message(
        self,
        *,
        compass_user_id: int,
        text: str,
        group_id: str | None = None,
        message_type: str | None = None,
        display_name: str | None = None,
    ) -> str:
        """
        Обрабатывает входящее сообщение и возвращает текст ответа.
        """

        message = text.strip()

        logger.info(
            "Received Compass message: user_id=%s, message=%r",
            compass_user_id,
            message,
        )

        if not message:
            return "Сообщение не может быть пустым."

        # Название команды всегда приводим к нижнему регистру.
        # Благодаря этому одинаково работают /Да, /ДА, /да и т. д.
        command_name = message.split(maxsplit=1)[0].lower()

        if command_name == "/ping":
            return "Sunshine Assistant работает ✅"

        if command_name == "/start":
            return self._get_start_message()

        if command_name == "/help":
            return self._get_help_message()

        if command_name == "/survey":
            return self._start_survey(
                compass_user_id=compass_user_id,
                display_name=display_name,
                group_id=group_id,
                message_type=message_type,
            )

        if command_name == "/cancel":
            return self._cancel_survey(
                compass_user_id=compass_user_id,
            )

        # Ответы на вопрос «Да или Нет».
        # Регистр команды значения не имеет.
        if command_name in {
            "/да",
            "/нет",
            "/yes",
            "/no",
        }:
            answer_value = command_name.removeprefix("/")

            logger.info(
                "Survey yes/no answer: user_id=%s, answer=%s",
                compass_user_id,
                answer_value,
            )

            return self._process_survey_answer(
                compass_user_id=compass_user_id,
                raw_answer=answer_value,
                display_name=display_name,
                group_id=group_id,
                message_type=message_type,
            )

        # Новая локация передаётся после команды /location.
        if command_name == "/location":
            parts = message.split(maxsplit=1)

            if len(parts) < 2 or not parts[1].strip():
                return (
                    "После команды /location нужно указать локацию.\n\n"
                    "Например:\n"
                    "/location Санкт-Петербург\n"
                    "/location офис Омск"
                )

            location = parts[1].strip()

            logger.info(
                "Survey location answer: user_id=%s, location=%r",
                compass_user_id,
                location,
            )

            return self._process_survey_answer(
                compass_user_id=compass_user_id,
                raw_answer=location,
                display_name=display_name,
                group_id=group_id,
                message_type=message_type,
            )

        active_session = self.survey_service.get_active_session(
            compass_user_id=compass_user_id,
        )

        # Не передаём неизвестную slash-команду в качестве ответа на опрос.
        if command_name.startswith("/"):
            if active_session is not None:
                return (
                    "Команда не распознана.\n\n"
                    "Для ответа используйте:\n"
                    "/да — если локация изменилась\n"
                    "/нет — если локация не изменилась\n"
                    "/location <город или офис> — указать новую локацию\n\n"
                    "Для отмены опроса отправьте /cancel."
                )

            return (
                "Неизвестная команда.\n\n"
                "Отправьте /help, чтобы увидеть список команд."
            )

        # Обычный текст Compass обычно не передаёт UserBot.
        # Этот блок оставлен как дополнительная защита.
        if active_session is not None:
            return (
                "Ответ должен начинаться с символа «/».\n\n"
                "Используйте одну из команд:\n"
                "/да\n"
                "/нет\n"
                "/location <город или офис>"
            )

        return (
            "Сейчас нет активного опроса.\n\n"
            "Чтобы начать, отправьте /survey."
        )

    def _start_survey(
        self,
        *,
        compass_user_id: int,
        display_name: str | None,
        group_id: str | None,
        message_type: str | None,
    ) -> str:
        try:
            result = self.survey_service.start_survey(
                compass_user_id=compass_user_id,
                survey_code=self.LOCATION_SURVEY_CODE,
                display_name=display_name,
                group_id=group_id,
                message_type=message_type,
            )

        except SurveyNotFoundError:
            logger.exception(
                "Survey not found: code=%s",
                self.LOCATION_SURVEY_CODE,
            )

            return (
                "Опрос пока недоступен.\n"
                "Обратитесь к администратору."
            )

        return result.message

    def _process_survey_answer(
        self,
        *,
        compass_user_id: int,
        raw_answer: str,
        display_name: str | None,
        group_id: str | None,
        message_type: str | None,
    ) -> str:
        try:
            result = self.survey_service.process_answer(
                compass_user_id=compass_user_id,
                raw_answer=raw_answer,
                display_name=display_name,
                group_id=group_id,
                message_type=message_type,
            )

            return result.message

        except AnswerValidationError as error:
            return str(error)

        except ActiveSurveyNotFoundError:
            return (
                "Активный опрос не найден.\n"
                "Чтобы начать новый опрос, отправьте /survey."
            )

    def _cancel_survey(
        self,
        *,
        compass_user_id: int,
    ) -> str:
        cancelled = self.survey_service.cancel_active_survey(
            compass_user_id=compass_user_id,
        )

        if cancelled:
            return (
                "Опрос отменён.\n"
                "Чтобы начать заново, отправьте /survey."
            )

        return "У вас нет активного опроса."

    @staticmethod
    def _get_start_message() -> str:
        return (
            "Здравствуйте! Я Sunshine Assistant ☀️\n\n"
            "Я помогаю проводить внутренние опросы.\n\n"
            "Чтобы начать опрос, отправьте /survey."
        )

    @staticmethod
    def _get_help_message() -> str:
        return (
            "Команды Sunshine Assistant:\n\n"
            "/survey — начать опрос\n"
            "/да — локация изменилась\n"
            "/нет — локация не изменилась\n"
            "/location <город или офис> — указать новую локацию\n"
            "/cancel — отменить опрос\n"
            "/ping — проверить работу бота\n"
            "/help — показать справку\n\n"
            "Регистр команд не имеет значения: "
            "/Да, /ДА и /да работают одинаково.\n\n"
            "Важно: Compass передаёт боту только сообщения, "
            "которые начинаются с символа «/»."
        )


__all__ = ["CompassBotService"]
