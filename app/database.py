from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings


engine = create_engine(settings.database_url)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def check_database() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
