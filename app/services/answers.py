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
