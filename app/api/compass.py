import logging
from typing import Any

from fastapi import APIRouter, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compass",
    tags=["Compass"],
)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
)
async def compass_webhook(request: Request) -> dict[str, Any]:
    payload = await request.json()

    logger.info(
        "Received Compass webhook: %s",
        payload,
    )

    return {
        "status": "ok",
    }
