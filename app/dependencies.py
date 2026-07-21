from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database import get_session_factory


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
