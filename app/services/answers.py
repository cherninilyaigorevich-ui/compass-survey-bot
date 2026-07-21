from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.survey_answer import SurveyAnswer


def save_answer(
    db: Session,
    user_id: str,
    username: str | None,
    answer: str,
    location: str | None,
) -> SurveyAnswer:

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


def get_answers(
    db: Session,
) -> list[SurveyAnswer]:

    return (
        db.query(SurveyAnswer).order_by(SurveyAnswer.created_at.desc()).limit(100).all()
    )


def get_answer_stats(
    db: Session,
) -> dict:

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
