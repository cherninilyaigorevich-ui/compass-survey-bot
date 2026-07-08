from sqlalchemy import func

from app.database import SessionLocal
from app.models.survey_answer import SurveyAnswer


def save_answer(
    user_id: str,
    username: str | None,
    answer: str,
    location: str | None,
) -> SurveyAnswer:
    db = SessionLocal()

    try:
        survey_answer = SurveyAnswer(
            user_id=user_id,
            username=username,
            answer=answer,
            location=location,
        )

        db.add(survey_answer)
        db.commit()
        db.refresh(survey_answer)

        return survey_answer

    finally:
        db.close()


def get_answers() -> list[SurveyAnswer]:
    db = SessionLocal()

    try:
        return (
            db.query(SurveyAnswer)
            .order_by(SurveyAnswer.created_at.desc())
            .limit(100)
            .all()
        )

    finally:
        db.close()


def get_answer_stats() -> dict:
    db = SessionLocal()

    try:
        total = db.query(func.count(SurveyAnswer.id)).scalar()

        yes_count = (
            db.query(func.count(SurveyAnswer.id))
            .filter(SurveyAnswer.answer == "yes")
            .scalar()
        )

        no_count = (
            db.query(func.count(SurveyAnswer.id))
            .filter(SurveyAnswer.answer == "no")
            .scalar()
        )

        return {
            "total": total,
            "yes": yes_count,
            "no": no_count,
        }

    finally:
        db.close()
