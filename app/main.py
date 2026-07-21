from fastapi import FastAPI

from app.api.answers import router as answers_router
from app.api.health import router as health_router

app = FastAPI(
    title="Compass Survey Bot",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(answers_router)
