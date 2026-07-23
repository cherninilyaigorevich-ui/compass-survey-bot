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
