from pydantic import BaseModel
from fastapi import APIRouter

from app.services.answers import save_answer

router = APIRouter(prefix="/answers", tags=["answers"])


class AnswerCreate(BaseModel):
    user_id: str
    username: str | None = None
    answer: str
    location: str | None = None


@router.post("")
def create_answer(payload: AnswerCreate):
    saved_answer = save_answer(
        user_id=payload.user_id,
        username=payload.username,
        answer=payload.answer,
        location=payload.location,
    )

    return {
        "id": saved_answer.id,
        "user_id": saved_answer.user_id,
        "username": saved_answer.username,
        "answer": saved_answer.answer,
        "location": saved_answer.location,
        "created_at": saved_answer.created_at,
    }
