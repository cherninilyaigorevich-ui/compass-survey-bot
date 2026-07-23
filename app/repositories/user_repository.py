from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.compass_user import CompassUser


class UserRepository:
    """Работа с пользователями Compass в PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> CompassUser | None:
        return self.db.get(CompassUser, user_id)

    def get_by_compass_user_id(
        self,
        compass_user_id: int,
    ) -> CompassUser | None:
        statement = select(CompassUser).where(
            CompassUser.compass_user_id == compass_user_id,
        )

        return self.db.scalar(statement)

    def create(
        self,
        *,
        compass_user_id: int,
        display_name: str | None = None,
        group_id: str | None = None,
        message_type: str | None = None,
    ) -> CompassUser:
        now = datetime.now(timezone.utc)

        user = CompassUser(
            compass_user_id=compass_user_id,
            display_name=display_name,
            last_group_id=group_id,
            last_message_type=message_type,
            created_at=now,
            last_seen_at=now,
        )

        self.db.add(user)
        self.db.flush()

        return user

    def get_or_create(
        self,
        *,
        compass_user_id: int,
        display_name: str | None = None,
        group_id: str | None = None,
        message_type: str | None = None,
    ) -> CompassUser:
        user = self.get_by_compass_user_id(compass_user_id)

        if user is None:
            return self.create(
                compass_user_id=compass_user_id,
                display_name=display_name,
                group_id=group_id,
                message_type=message_type,
            )

        self.update_webhook_data(
            user=user,
            display_name=display_name,
            group_id=group_id,
            message_type=message_type,
        )

        return user

    def update_webhook_data(
        self,
        *,
        user: CompassUser,
        display_name: str | None = None,
        group_id: str | None = None,
        message_type: str | None = None,
    ) -> CompassUser:
        if display_name:
            user.display_name = display_name

        if group_id:
            user.last_group_id = group_id

        if message_type:
            user.last_message_type = message_type

        user.last_seen_at = datetime.now(timezone.utc)

        self.db.flush()

        return user

    def update_location(
        self,
        *,
        user: CompassUser,
        location: str,
    ) -> CompassUser:
        normalized_location = location.strip()

        if not normalized_location:
            raise ValueError("Location cannot be empty")

        user.current_location = normalized_location
        user.last_seen_at = datetime.now(timezone.utc)

        self.db.flush()

        return user

    def list_all(self) -> list[CompassUser]:
        statement = select(CompassUser).order_by(CompassUser.id)

        return list(self.db.scalars(statement).all())
