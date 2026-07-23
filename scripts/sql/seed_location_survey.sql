BEGIN;

-- ============================================================
-- 1. Создание или обновление опроса
-- ============================================================

INSERT INTO surveys (
    code,
    title,
    description,
    completion_message,
    interval_days,
    enabled,
    created_at,
    updated_at
)
VALUES (
    'location_check',
    'Проверка рабочей локации',
    'Периодический HR-опрос для проверки текущей рабочей локации сотрудника.',
    'Спасибо! Информация о рабочей локации сохранена ✅',
    90,
    TRUE,
    NOW(),
    NOW()
)
ON CONFLICT (code)
DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    completion_message = EXCLUDED.completion_message,
    interval_days = EXCLUDED.interval_days,
    enabled = EXCLUDED.enabled,
    updated_at = NOW();


-- ============================================================
-- 2. Первый вопрос
-- ============================================================

INSERT INTO survey_questions (
    survey_id,
    code,
    position,
    text,
    answer_type,
    required,
    show_if_question_id,
    show_if_value
)
SELECT
    surveys.id,
    'location_changed',
    1,
    'Изменилась ли ваша рабочая локация?',
    'yes_no',
    TRUE,
    NULL,
    NULL
FROM surveys
WHERE surveys.code = 'location_check'
ON CONFLICT (survey_id, code)
DO UPDATE SET
    position = EXCLUDED.position,
    text = EXCLUDED.text,
    answer_type = EXCLUDED.answer_type,
    required = EXCLUDED.required,
    show_if_question_id = NULL,
    show_if_value = NULL;


-- ============================================================
-- 3. Второй условный вопрос
--
-- Показывается только тогда, когда на первый вопрос
-- пользователь ответил нормализованным значением "yes".
-- ============================================================

INSERT INTO survey_questions (
    survey_id,
    code,
    position,
    text,
    answer_type,
    required,
    show_if_question_id,
    show_if_value
)
SELECT
    survey.id,
    'new_location',
    2,
    'Укажите вашу новую рабочую локацию.',
    'text',
    TRUE,
    first_question.id,
    'yes'
FROM surveys AS survey
JOIN survey_questions AS first_question
    ON first_question.survey_id = survey.id
   AND first_question.code = 'location_changed'
WHERE survey.code = 'location_check'
ON CONFLICT (survey_id, code)
DO UPDATE SET
    position = EXCLUDED.position,
    text = EXCLUDED.text,
    answer_type = EXCLUDED.answer_type,
    required = EXCLUDED.required,
    show_if_question_id = EXCLUDED.show_if_question_id,
    show_if_value = EXCLUDED.show_if_value;

COMMIT;
SQL
