#!/usr/bin/env bash

set -euo pipefail

cd /opt/compass-survey-bot

BACKUP_DIR="backup-broadcast-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"

cp app/config.py "$BACKUP_DIR/config.py"
cp app/main.py "$BACKUP_DIR/main.py"
cp app/services/__init__.py "$BACKUP_DIR/services-init.py"
cp requirements.txt "$BACKUP_DIR/requirements.txt"

mkdir -p app/scheduler

cat > requirements.txt <<'EOF'
fastapi==0.139.2
uvicorn[standard]==0.51.0
pydantic-settings==2.14.2
sqlalchemy==2.0.51
psycopg2-binary==2.9.12
alembic==1.16.5
pytest==9.1.1
httpx==0.28.1
APScheduler==3.11.3
ruff
EOF

cat > app/config.py <<'PY'
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "Compass Survey Bot"
    app_version: str = "0.1.0"
    environment: str = "development"

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    compass_bot_token: str | None = None
    compass_api_base_url: str = (
        "https://userbot.getcompass.com/api/v3"
    )
    compass_request_timeout_seconds: float = 15.0

    survey_broadcast_enabled: bool = False
    survey_broadcast_interval_minutes: int = 2
    survey_broadcast_initial_delay_seconds: int = 10
    survey_broadcast_survey_code: str = "location_check"
    survey_broadcast_cancel_active: bool = True

    # Если указан ID, рассылка выполняется только этому пользователю.
    # Удалите параметр из .env после завершения тестирования.
    survey_broadcast_only_user_id: int | None = None

    # Уникальный ключ PostgreSQL advisory lock.
    # Он предотвращает одновременный запуск рассылки
    # несколькими экземплярами приложения.
    survey_broadcast_lock_key: int = 741852963

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


settings = Settings()
PY

cat > app/services/survey_broadcast.py <<'PY'
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
PY

cat > app/scheduler/jobs.py <<'PY'
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
PY

cat > app/scheduler/runtime.py <<'PY'
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.scheduler.jobs import run_survey_broadcast_job

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    interval_minutes = (
        settings.survey_broadcast_interval_minutes
    )

    if interval_minutes <= 0:
        raise ValueError(
            "SURVEY_BROADCAST_INTERVAL_MINUTES "
            "должен быть больше нуля."
        )

    initial_delay_seconds = (
        settings.survey_broadcast_initial_delay_seconds
    )

    if initial_delay_seconds < 0:
        raise ValueError(
            "SURVEY_BROADCAST_INITIAL_DELAY_SECONDS "
            "не может быть отрицательным."
        )

    scheduler = AsyncIOScheduler(
        timezone=timezone.utc,
    )

    scheduler.add_job(
        run_survey_broadcast_job,
        trigger=IntervalTrigger(
            minutes=interval_minutes,
            timezone=timezone.utc,
        ),
        id="survey-broadcast",
        name="Compass survey broadcast",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60,
        next_run_time=(
            datetime.now(timezone.utc)
            + timedelta(seconds=initial_delay_seconds)
        ),
    )

    return scheduler


@asynccontextmanager
async def scheduler_lifespan() -> AsyncIterator[None]:
    if not settings.survey_broadcast_enabled:
        logger.info(
            "Survey broadcast scheduler is disabled"
        )

        yield
        return

    scheduler = create_scheduler()
    scheduler.start()

    logger.info(
        "Survey broadcast scheduler started: "
        "interval_minutes=%s, survey_code=%s, "
        "only_user_id=%s",
        settings.survey_broadcast_interval_minutes,
        settings.survey_broadcast_survey_code,
        settings.survey_broadcast_only_user_id,
    )

    try:
        yield

    finally:
        scheduler.shutdown(wait=False)

        logger.info(
            "Survey broadcast scheduler stopped"
        )


__all__ = [
    "create_scheduler",
    "scheduler_lifespan",
]
PY

cat > app/scheduler/__init__.py <<'PY'
from app.scheduler.jobs import run_survey_broadcast_job
from app.scheduler.runtime import (
    create_scheduler,
    scheduler_lifespan,
)

__all__ = [
    "create_scheduler",
    "run_survey_broadcast_job",
    "scheduler_lifespan",
]
PY

cat > app/services/__init__.py <<'PY'
from app.services.answer_normalizer import (
    AnswerValidationError,
    normalize_answer,
    normalize_text,
    normalize_yes_no,
)
from app.services.compass_bot import CompassBotService
from app.services.compass_client import (
    CompassApiError,
    CompassClient,
    CompassClientError,
    CompassConfigurationError,
    CompassRequestError,
    CompassSendResult,
)
from app.services.survey_broadcast import (
    SurveyBroadcastResult,
    SurveyBroadcastService,
)
from app.services.survey_service import (
    ActiveSurveyNotFoundError,
    SurveyNotFoundError,
    SurveyResult,
    SurveyService,
    SurveyServiceError,
)

__all__ = [
    "ActiveSurveyNotFoundError",
    "AnswerValidationError",
    "CompassApiError",
    "CompassBotService",
    "CompassClient",
    "CompassClientError",
    "CompassConfigurationError",
    "CompassRequestError",
    "CompassSendResult",
    "SurveyBroadcastResult",
    "SurveyBroadcastService",
    "SurveyNotFoundError",
    "SurveyResult",
    "SurveyService",
    "SurveyServiceError",
    "normalize_answer",
    "normalize_text",
    "normalize_yes_no",
]
PY

python3 - <<'PY'
from pathlib import Path

path = Path("app/main.py")
content = path.read_text(encoding="utf-8")

scheduler_import = (
    "from app.scheduler import scheduler_lifespan\n"
)

survey_seed_import = (
    "from app.services.survey_seed import "
    "seed_location_survey\n"
)

if scheduler_import not in content:
    if survey_seed_import not in content:
        raise RuntimeError(
            "Не найдена строка импорта survey_seed в app/main.py"
        )

    content = content.replace(
        survey_seed_import,
        scheduler_import + survey_seed_import,
        1,
    )

old_lifespan_end = (
    "    yield\n\n"
    "    logger.info(\"%s stopped\", settings.app_name)"
)

new_lifespan_end = (
    "    async with scheduler_lifespan():\n"
    "        yield\n\n"
    "    logger.info(\"%s stopped\", settings.app_name)"
)

if new_lifespan_end not in content:
    if old_lifespan_end not in content:
        raise RuntimeError(
            "Не найден блок yield в lifespan app/main.py"
        )

    content = content.replace(
        old_lifespan_end,
        new_lifespan_end,
        1,
    )

path.write_text(content, encoding="utf-8")
PY

python3 - <<'PY'
from pathlib import Path

env_path = Path(".env")

if not env_path.exists():
    raise RuntimeError("Файл .env не найден")

settings_to_write = {
    "SURVEY_BROADCAST_ENABLED": "true",
    "SURVEY_BROADCAST_INTERVAL_MINUTES": "2",
    "SURVEY_BROADCAST_INITIAL_DELAY_SECONDS": "10",
    "SURVEY_BROADCAST_SURVEY_CODE": "location_check",
    "SURVEY_BROADCAST_CANCEL_ACTIVE": "true",
    "SURVEY_BROADCAST_ONLY_USER_ID": "263107",
    "COMPASS_REQUEST_TIMEOUT_SECONDS": "15",
}

lines = env_path.read_text(encoding="utf-8").splitlines()

result = []
updated_keys = set()

for line in lines:
    stripped = line.strip()

    if (
        not stripped
        or stripped.startswith("#")
        or "=" not in line
    ):
        result.append(line)
        continue

    key = line.split("=", maxsplit=1)[0].strip()

    if key in settings_to_write:
        result.append(
            f"{key}={settings_to_write[key]}"
        )
        updated_keys.add(key)
    else:
        result.append(line)

for key, value in settings_to_write.items():
    if key not in updated_keys:
        result.append(f"{key}={value}")

env_path.write_text(
    "\n".join(result) + "\n",
    encoding="utf-8",
)
PY

sudo find app -type d -name __pycache__ \
    -prune -exec rm -rf {} + 2>/dev/null || true

echo
echo "Файлы установлены."
echo "Резервные копии: $BACKUP_DIR"
