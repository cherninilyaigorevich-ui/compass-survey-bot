import logging

from sqlalchemy import text

from app.config import settings
from app.database import get_engine, get_session_factory
from app.services.survey_broadcast import SurveyBroadcastService

logger = logging.getLogger(__name__)


async def run_survey_broadcast_job() -> None:
    """
    Запускает рассылку под PostgreSQL advisory lock.

    Блокировка не позволяет нескольким экземплярам приложения
    одновременно отправить один и тот же опрос.
    """

    engine = get_engine()
    lock_key = settings.survey_broadcast_lock_key

    with engine.connect() as connection:
        lock_acquired = bool(
            connection.scalar(
                text(
                    "SELECT pg_try_advisory_lock(:lock_key)"
                ),
                {
                    "lock_key": lock_key,
                },
            )
        )

        if not lock_acquired:
            logger.info(
                "Survey broadcast skipped: "
                "another application instance holds the lock"
            )
            return

        try:
            service = SurveyBroadcastService(
                session_factory=get_session_factory(),
            )

            result = await service.broadcast()

            logger.info(
                "Scheduled survey broadcast result: "
                "total=%s, sent=%s, failed=%s",
                result.total_users,
                result.sent,
                result.failed,
            )

        except Exception:
            logger.exception(
                "Scheduled survey broadcast job failed"
            )

        finally:
            try:
                connection.execute(
                    text(
                        "SELECT pg_advisory_unlock(:lock_key)"
                    ),
                    {
                        "lock_key": lock_key,
                    },
                )

            except Exception:
                logger.exception(
                    "Unable to release survey broadcast lock"
                )


__all__ = ["run_survey_broadcast_job"]
