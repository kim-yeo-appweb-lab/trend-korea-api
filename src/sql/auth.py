from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.enums import UserRole
from src.models.auth import RefreshToken
from src.models.users import User


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_nickname(self, nickname: str) -> User | None:
        stmt = select(User).where(User.nickname == nickname)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_user(self, *, nickname: str, email: str, password_hash: str) -> User:
        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid4()),
            nickname=nickname,
            email=email,
            password_hash=password_hash,
            role=UserRole.MEMBER,
            is_active=True,
            profile_image=None,
            withdrawn_at=None,
            created_at=now,
            updated_at=now,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def create_refresh_token(
        self,
        *,
        user_id: str,
        token_hash: str,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        now = datetime.now(timezone.utc)
        token = RefreshToken(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expires_at,
            created_at=now,
        )
        self.db.add(token)
        self.db.flush()
        return token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke_refresh_token(self, token_hash: str) -> None:
        token = self.get_refresh_token_by_hash(token_hash)
        if token and token.revoked_at is None:
            token.revoked_at = datetime.now(timezone.utc)
            self.db.flush()

    def deactivate_user(self, user_id: str) -> None:
        user = self.get_user_by_id(user_id)
        if user:
            now = datetime.now(timezone.utc)
            user.withdrawn_at = now
            user.is_active = False
            self.db.flush()

    def revoke_refresh_tokens_by_user_id(self, user_id: str) -> None:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        rows = self.db.execute(stmt).scalars().all()
        if not rows:
            return

        now = datetime.now(timezone.utc)
        for token in rows:
            token.revoked_at = now
        self.db.flush()
