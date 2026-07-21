from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings


def get_engine():
    return create_engine(settings.database_url)


def get_session_factory():
    engine = get_engine()

    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )


def check_database() -> bool:
    engine = get_engine()

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
