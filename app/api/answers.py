from pydantic import BaseModel, field_validator
from fastapi import APIRouter

from app.services.answers import get_answer_stats, get_answers, save_answer

router = APIRouter(prefix="/answers", tags=["answers"])


class AnswerCreate(BaseModel):
    user_id: str
    username: str | None = None
    answer: str
    location: str | None = None

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        normalized = value.strip().lower()

        if normalized not in ("yes", "no"):
            raise ValueError("answer must be 'yes' or 'no'")

        return normalized


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


@router.get("")
def list_answers():
    answers = get_answers()

    return [
        {
            "id": item.id,
            "user_id": item.user_id,
            "username": item.username,
            "answer": item.answer,
            "location": item.location,
            "created_at": item.created_at,
        }
        for item in answers
    ]


@router.get("/stats")
def stats():
    return get_answer_stats()
