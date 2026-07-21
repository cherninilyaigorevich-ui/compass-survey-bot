import os
import subprocess

import pytest

from app.database import get_engine
from app.models.survey_answer import Base

os.environ.setdefault("POSTGRES_DB", "compass_test")
os.environ.setdefault("POSTGRES_USER", "compass_test")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")

def pytest_sessionstart(session):
    """
    Выполняется один раз перед запуском всех тестов.
    Применяем миграции к тестовой БД.
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
