import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.repositories import UserRepository
from app.services.compass_client import (
    CompassClient,
    CompassClientError,
)
from app.services.survey_service import (
    SurveyNotFoundError,
    SurveyService,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SurveyBroadcastResult:
    total_users: int = 0
    prepared: int = 0
    sent: int = 0
    failed: int = 0


class SurveyBroadcastService:
    """Автоматическая рассылка опроса пользователям Compass."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        compass_client: CompassClient | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.compass_client = compass_client or CompassClient(
            timeout_seconds=(
                settings.compass_request_timeout_seconds
            ),
        )

    async def broadcast(self) -> SurveyBroadcastResult:
        recipients = self._get_recipients()

        result = SurveyBroadcastResult(
            total_users=len(recipients),
        )

        if not recipients:
            logger.info(
                "Survey broadcast skipped: no Compass users found"
            )
            return result

        logger.info(
            "Survey broadcast started: survey_code=%s, users=%s",
            settings.survey_broadcast_survey_code,
            len(recipients),
        )

        for compass_user_id, display_name in recipients:
            try:
                message = self._prepare_survey_message(
                    compass_user_id=compass_user_id,
                    display_name=display_name,
                )

                result.prepared += 1

                await self.compass_client.send_text_message(
                    user_id=compass_user_id,
                    text=message,
                )

                result.sent += 1

                logger.info(
                    "Survey broadcast message sent: user_id=%s",
                    compass_user_id,
                )

            except SurveyNotFoundError:
                result.failed += 1

                logger.exception(
                    "Survey broadcast failed: survey %r not found",
                    settings.survey_broadcast_survey_code,
                )

                # Останавливаем рассылку: ошибка общая для всех
                # пользователей, повторять её для каждого нет смысла.
                break

            except CompassClientError:
                result.failed += 1

                logger.exception(
                    "Compass API error during survey broadcast: "
                    "user_id=%s",
                    compass_user_id,
                )

            except Exception:
                result.failed += 1

                logger.exception(
                    "Unexpected survey broadcast error: user_id=%s",
                    compass_user_id,
                )

        logger.info(
            "Survey broadcast completed: "
            "total=%s, prepared=%s, sent=%s, failed=%s",
            result.total_users,
            result.prepared,
            result.sent,
            result.failed,
        )

        return result

    def _get_recipients(
        self,
    ) -> list[tuple[int, str | None]]:
        with self.session_factory() as db:
            users = UserRepository(db).list_all()

            only_user_id = (
                settings.survey_broadcast_only_user_id
            )

            recipients = [
                (
                    int(user.compass_user_id),
                    user.display_name,
                )
                for user in users
                if (
                    only_user_id is None
                    or user.compass_user_id == only_user_id
                )
            ]

        return recipients

    def _prepare_survey_message(
        self,
        *,
        compass_user_id: int,
        display_name: str | None,
    ) -> str:
        with self.session_factory() as db:
            try:
                service = SurveyService(db)

                if settings.survey_broadcast_cancel_active:
                    cancelled = service.cancel_active_survey(
                        compass_user_id=compass_user_id,
                    )

                    if cancelled:
                        logger.info(
                            "Previous active survey cancelled: "
                            "user_id=%s",
                            compass_user_id,
                        )

                survey_result = service.start_survey(
                    compass_user_id=compass_user_id,
                    survey_code=(
                        settings.survey_broadcast_survey_code
                    ),
                    display_name=display_name,
                    message_type="text",
                )

                db.commit()

                return survey_result.message

            except Exception:
                db.rollback()
                raise


__all__ = [
    "SurveyBroadcastResult",
    "SurveyBroadcastService",
]
