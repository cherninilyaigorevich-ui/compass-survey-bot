import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.answers import router as answers_router
from app.api.health import router as health_router
from app.config import settings
from app.core.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("%s started", settings.app_name)

    logger.info("Version: %s", settings.app_version)

    logger.info("Environment: %s", settings.environment)

    yield

    logger.info("%s stopped", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(answers_router)
