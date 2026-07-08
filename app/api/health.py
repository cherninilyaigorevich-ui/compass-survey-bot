from fastapi import APIRouter

from app.database import check_database

router = APIRouter()


@router.get("/health")
def healthcheck():
    check_database()
    return {
        "status": "ok",
        "database": "ok",
    }
