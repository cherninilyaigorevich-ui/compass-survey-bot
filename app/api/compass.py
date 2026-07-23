import hmac
import logging
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db
from app.services import CompassBotService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/compass",
    tags=["Compass"],
)


class CompassWebhookPayload(BaseModel):
    group_id: str = ""
    message_id: str
    text: str = Field(min_length=1)
    type: Literal["single", "group"]
    user_id: int


class CompassMessagePost(BaseModel):
    text: str
    type: Literal["text"] = "text"


class CompassWebhookAnswer(BaseModel):
    action: Literal["message_send"] = "message_send"
    post: CompassMessagePost


class CompassWebhookResponse(BaseModel):
    answer: CompassWebhookAnswer


def verify_compass_token(
    authorization: str | None,
) -> None:
    """Проверяет Bearer-токен входящего webhook Compass."""

    expected_authorization = (
        f"Bearer {settings.compass_bot_token}"
    )

    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    if not hmac.compare_digest(
        authorization.encode("utf-8"),
        expected_authorization.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Compass bot token",
        )


def build_message(text: str) -> CompassWebhookResponse:
    """Создаёт ответ в формате Compass webhook API."""

    return CompassWebhookResponse(
        answer=CompassWebhookAnswer(
            post=CompassMessagePost(
                text=text,
            ),
        ),
    )


@router.post(
    "/webhook",
    response_model=CompassWebhookResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def compass_webhook(
    payload: CompassWebhookPayload,
    authorization: Annotated[
        str | None,
        Header(alias="Authorization"),
    ] = None,
    db: Session = Depends(get_db),
) -> CompassWebhookResponse:
    verify_compass_token(authorization)

    logger.warning(
        "WEBHOOK BODY: user_id=%s type=%s text=%r group_id=%s message_id=%s",
        payload.user_id,
        payload.type,
        payload.text,
        payload.group_id,
        payload.message_id,
    )

    short_message_id = (
        f"{payload.message_id[:16]}..."
        if len(payload.message_id) > 16
        else payload.message_id
    )

    logger.info(
        "Compass message received: "
        "user_id=%s type=%s message_id=%s",
        payload.user_id,
        payload.type,
        short_message_id,
    )

    service = CompassBotService(db)

    try:
        response_text = service.process_message(
            compass_user_id=payload.user_id,
            text=payload.text,
            group_id=payload.group_id or None,
            message_type=payload.type,
        )

        db.commit()

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to process Compass message: "
            "user_id=%s message_id=%s",
            payload.user_id,
            short_message_id,
        )

        return build_message(
            "Произошла внутренняя ошибка.\n"
            "Попробуйте повторить сообщение позднее."
        )

    return build_message(response_text)
