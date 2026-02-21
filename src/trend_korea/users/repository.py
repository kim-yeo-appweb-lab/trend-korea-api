from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from trend_korea.users.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_nickname(self, nickname: str) -> User | None:
        stmt = select(User).where(User.nickname == nickname)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_profile(
        self,
        user: User,
        *,
        nickname: str | None,
        profile_image: str | None,
    ) -> User:
        if nickname is not None:
            user.nickname = nickname
        if profile_image is not None:
            user.profile_image = profile_image
        user.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return user
