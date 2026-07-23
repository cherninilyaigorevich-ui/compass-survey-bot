from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_engine() -> Engine:
    """Возвращает общий SQLAlchemy Engine приложения."""

    return engine


def get_session_factory() -> sessionmaker[Session]:
    """Возвращает общую фабрику синхронных сессий."""

    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency для получения сессии БД.

    Сессия автоматически закрывается после обработки запроса.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def check_database() -> bool:
    """Проверяет доступность PostgreSQL простым запросом SELECT 1."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
