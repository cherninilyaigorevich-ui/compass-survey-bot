import subprocess

import pytest

from app.database import get_engine
from app.models.survey_answer import Base


def pytest_sessionstart(session: pytest.Session) -> None:
    """
    Выполняется один раз перед запуском тестов.
    Применяет миграции к базе данных.
    """

    subprocess.run(
        [
            "alembic",
            "upgrade",
            "head",
        ],
        check=True,
    )


@pytest.fixture(autouse=True)
def clean_database():
    """
    Очищает таблицы после каждого теста.
    """

    yield

    engine = get_engine()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
