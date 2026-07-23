class AnswerValidationError(ValueError):
    """Ошибка проверки пользовательского ответа."""


YES_VALUES = {
    "да",
    "/да",
    "ага",
    "угу",
    "конечно",
    "верно",
    "yes",
    "/yes",
    "y",
    "+",
    "1",
}


NO_VALUES = {
    "нет",
    "/нет",
    "неа",
    "не",
    "no",
    "/no",
    "n",
    "-",
    "0",
}


def normalize_yes_no(value: str) -> str:
    """
    Преобразует пользовательский ответ в значение yes или no.
    Поддерживает команды Compass:
    /да
    /нет
    """

    normalized = (
        value
        .strip()
        .lower()
        .replace("ё", "е")
    )

    if normalized in YES_VALUES:
        return "yes"

    if normalized in NO_VALUES:
        return "no"

    raise AnswerValidationError(
        "Ответьте командой:\n"
        "/да — если локация изменилась\n"
        "/нет — если локация не изменилась."
    )


def normalize_text(
    value: str,
    *,
    max_length: int | None = None,
) -> str:
    """
    Очищает обычный текстовый ответ.
    """

    normalized = " ".join(
        value.strip().split()
    )

    if not normalized:
        raise AnswerValidationError(
            "Ответ не может быть пустым."
        )

    if max_length is not None and len(normalized) > max_length:
        raise AnswerValidationError(
            f"Ответ слишком длинный. Максимум: {max_length} символов."
        )

    return normalized


def normalize_answer(
    *,
    answer_type: str,
    value: str,
    max_length: int | None = None,
) -> str:
    """
    Нормализует ответ в зависимости от типа вопроса.
    """

    normalized_type = (
        answer_type
        .strip()
        .lower()
    )

    if normalized_type == "yes_no":
        return normalize_yes_no(value)

    if normalized_type == "text":
        return normalize_text(
            value,
            max_length=max_length,
        )

    raise AnswerValidationError(
        f"Неподдерживаемый тип вопроса: {answer_type}"
    )
