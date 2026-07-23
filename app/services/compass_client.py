import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class CompassClientError(RuntimeError):
    """Базовая ошибка клиента Compass UserBot API."""


class CompassConfigurationError(CompassClientError):
    """Ошибка конфигурации Compass UserBot API."""


class CompassRequestError(CompassClientError):
    """Ошибка HTTP-запроса к Compass UserBot API."""


class CompassApiError(CompassClientError):
    """Compass API вернул ответ со статусом error."""

    def __init__(
        self,
        message: str,
        *,
        error_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.error_code = error_code
        self.response_data = response_data or {}


@dataclass(slots=True, frozen=True)
class CompassSendResult:
    """
    Результат успешной отправки сообщения.

    message_id — идентификатор созданного сообщения Compass.
    """

    message_id: str


class CompassClient:
    """Асинхронный клиент Compass UserBot API."""

    SEND_MESSAGE_PATH = "/user/send"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        resolved_base_url = (
            base_url
            if base_url is not None
            else settings.compass_api_base_url
        )

        resolved_token = (
            token
            if token is not None
            else settings.compass_bot_token
        )

        self.base_url = str(resolved_base_url).rstrip("/")
        self.token = (
            str(resolved_token).strip()
            if resolved_token is not None
            else ""
        )
        self.timeout_seconds = timeout_seconds

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        if not self.base_url:
            raise CompassConfigurationError(
                "Не задан COMPASS_API_BASE_URL."
            )

        if not self.token:
            raise CompassConfigurationError(
                "Не задан COMPASS_BOT_TOKEN."
            )

        if self.timeout_seconds <= 0:
            raise CompassConfigurationError(
                "Тайм-аут Compass API должен быть больше нуля."
            )

    async def send_text_message(
        self,
        *,
        user_id: int,
        text: str,
    ) -> CompassSendResult:
        """
        Отправляет текстовое сообщение пользователю Compass.

        Endpoint:
        POST /user/send
        """

        if user_id <= 0:
            raise ValueError(
                "Compass user_id должен быть положительным числом."
            )

        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError(
                "Нельзя отправить пустое сообщение."
            )

        request_url = f"{self.base_url}{self.SEND_MESSAGE_PATH}"

        request_payload = {
            "user_id": user_id,
            "text": normalized_text,
            "type": "text",
        }

        request_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info(
            "Sending Compass message: user_id=%s, text_length=%s",
            user_id,
            len(normalized_text),
        )

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds),
            ) as client:
                response = await client.post(
                    request_url,
                    headers=request_headers,
                    json=request_payload,
                )

        except httpx.TimeoutException as error:
            raise CompassRequestError(
                "Превышено время ожидания ответа Compass API."
            ) from error

        except httpx.RequestError as error:
            raise CompassRequestError(
                f"Не удалось выполнить запрос к Compass API: {error}"
            ) from error

        response_data = self._decode_response(response)

        if response.status_code >= 400:
            error_message = self._extract_error_message(
                response_data=response_data,
                default=(
                    "Compass API вернул HTTP-ошибку "
                    f"{response.status_code}."
                ),
            )

            raise CompassRequestError(error_message)

        status_value = response_data.get("status")

        if status_value != "ok":
            api_response = response_data.get("response")

            if not isinstance(api_response, dict):
                api_response = {}

            error_code = api_response.get("error_code")

            if not isinstance(error_code, int):
                error_code = None

            error_message = self._extract_error_message(
                response_data=response_data,
                default="Compass API не смог отправить сообщение.",
            )

            raise CompassApiError(
                error_message,
                error_code=error_code,
                response_data=response_data,
            )

        api_response = response_data.get("response")

        if not isinstance(api_response, dict):
            raise CompassApiError(
                "Compass API вернул некорректный блок response.",
                response_data=response_data,
            )

        message_id = api_response.get("message_id")

        if not isinstance(message_id, str) or not message_id:
            raise CompassApiError(
                "Compass API не вернул message_id.",
                response_data=response_data,
            )

        logger.info(
            "Compass message sent successfully: "
            "user_id=%s, message_id=%s",
            user_id,
            self._shorten_message_id(message_id),
        )

        return CompassSendResult(
            message_id=message_id,
        )

    @staticmethod
    def _decode_response(
        response: httpx.Response,
    ) -> dict[str, Any]:
        try:
            response_data = response.json()

        except ValueError as error:
            raise CompassRequestError(
                "Compass API вернул ответ не в формате JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise CompassRequestError(
                "Compass API вернул некорректный JSON-ответ."
            )

        return response_data

    @staticmethod
    def _extract_error_message(
        *,
        response_data: dict[str, Any],
        default: str,
    ) -> str:
        api_response = response_data.get("response")

        if isinstance(api_response, dict):
            message = api_response.get("message")

            if isinstance(message, str) and message.strip():
                return message.strip()

        message = response_data.get("message")

        if isinstance(message, str) and message.strip():
            return message.strip()

        return default

    @staticmethod
    def _shorten_message_id(
        message_id: str,
    ) -> str:
        if len(message_id) <= 20:
            return message_id

        return f"{message_id[:20]}..."


__all__ = [
    "CompassApiError",
    "CompassClient",
    "CompassClientError",
    "CompassConfigurationError",
    "CompassRequestError",
    "CompassSendResult",
]
