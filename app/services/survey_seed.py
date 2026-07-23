from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.survey import Survey
from app.models.survey_question import SurveyQuestion

LOCATION_SURVEY_CODE = "location_check"


def seed_location_survey(db: Session) -> Survey:
    """
    Создаёт или обновляет опрос проверки рабочей локации.

    Повторный запуск безопасен:
    существующий опрос и вопросы будут обновлены.
    """

    survey = db.scalar(
        select(Survey).where(
            Survey.code == LOCATION_SURVEY_CODE,
        )
    )

    if survey is None:
        survey = Survey(
            code=LOCATION_SURVEY_CODE,
            title="Проверка рабочей локации",
            description=(
                "Периодический HR-опрос для проверки "
                "текущей рабочей локации сотрудника."
            ),
            completion_message=(
                "Спасибо! Информация о рабочей локации сохранена ✅"
            ),
            interval_days=90,
            enabled=True,
        )

        db.add(survey)
        db.flush()

    else:
        survey.title = "Проверка рабочей локации"
        survey.description = (
            "Периодический HR-опрос для проверки "
            "текущей рабочей локации сотрудника."
        )
        survey.completion_message = (
            "Спасибо! Информация о рабочей локации сохранена ✅"
        )
        survey.interval_days = 90
        survey.enabled = True

        db.flush()


    first_question = db.scalar(
        select(SurveyQuestion).where(
            SurveyQuestion.survey_id == survey.id,
            SurveyQuestion.code == "location_changed",
        )
    )

    first_question_text = (
    "Шаг 1 из 2.\n\n"
    "Изменилась ли ваша рабочая локация?\n\n"
    "Введите один из вариантов ответа:\n\n"
    "👉 /да — если локация изменилась\n"
    "👉 /нет — если локация осталась прежней\n\n"
    "Важно: обязательно используйте символ / перед командой."

    )

    if first_question is None:
        first_question = SurveyQuestion(
            survey_id=survey.id,
            code="location_changed",
            position=1,
            text=first_question_text,
            answer_type="yes_no",
            required=True,
            show_if_question_id=None,
            show_if_value=None,
        )

        db.add(first_question)
        db.flush()

    else:
        first_question.position = 1
        first_question.text = first_question_text
        first_question.answer_type = "yes_no"
        first_question.required = True
        first_question.show_if_question_id = None
        first_question.show_if_value = None

        db.flush()


    second_question = db.scalar(
        select(SurveyQuestion).where(
            SurveyQuestion.survey_id == survey.id,
            SurveyQuestion.code == "new_location",
        )
    )


    second_question_text = (
    "Шаг 2 из 2.\n\n"
    "Укажите новую рабочую локацию.\n\n"
    "Используйте команду:\n\n"
    "👉 /location <ваша локация>\n\n"
    "Примеры:\n"
    "/location Санкт-Петербург\n"
    "/location офис Омск\n\n"
    "Важно: обязательно используйте символ /."
    )

    if second_question is None:
        second_question = SurveyQuestion(
            survey_id=survey.id,
            code="new_location",
            position=2,
            text=second_question_text,
            answer_type="text",
            required=True,
            show_if_question_id=first_question.id,
            show_if_value="yes",
        )

        db.add(second_question)

    else:
        second_question.position = 2
        second_question.text = second_question_text
        second_question.answer_type = "text"
        second_question.required = True
        second_question.show_if_question_id = first_question.id
        second_question.show_if_value = "yes"


    db.flush()

    return survey
