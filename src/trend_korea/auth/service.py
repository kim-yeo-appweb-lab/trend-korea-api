from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from trend_korea.core.config import get_settings
from trend_korea.core.exceptions import AppError
from trend_korea.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from trend_korea.auth.repository import AuthRepository


@dataclass(slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    access_expires_in: int
    access_expires_at: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def register(self, *, nickname: str, email: str, password: str) -> AuthTokens:
        existing = self.repository.get_user_by_email(email)
        if existing is not None:
            raise AppError(
                code="E_CONFLICT_001",
                message="이미 가입된 이메일입니다.",
                status_code=409,
                details={"field": "email"},
            )

        existing_nickname = self.repository.get_user_by_nickname(nickname)
        if existing_nickname is not None:
            raise AppError(
                code="E_CONFLICT_002",
                message="이미 사용 중인 닉네임입니다.",
                status_code=409,
                details={"field": "nickname"},
            )

        user = self.repository.create_user(
            nickname=nickname,
            email=email,
            password_hash=hash_password(password),
        )
        return self._issue_tokens(user.id, user.role.value)

    def login(self, *, email: str, password: str) -> AuthTokens:
        user = self.repository.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AppError(
                code="E_AUTH_004",
                message="이메일 또는 비밀번호가 일치하지 않습니다.",
                status_code=401,
            )
        if user.withdrawn_at is not None:
            raise AppError(
                code="E_AUTH_006",
                message="이미 탈퇴한 계정입니다.",
                status_code=401,
            )
        return self._issue_tokens(user.id, user.role.value)

    def refresh(self, *, refresh_token: str) -> AuthTokens:
        payload = decode_token(refresh_token)
        if payload.get("typ") != "refresh":
            raise AppError(
                code="E_AUTH_003",
                message="유효하지 않은 토큰입니다.",
                status_code=401,
            )

        token_hash = hash_token(refresh_token)
        token_row = self.repository.get_refresh_token_by_hash(token_hash)
        if (
            token_row is None
            or token_row.revoked_at is not None
            or token_row.jti != payload.jti
        ):
            raise AppError(
                code="E_AUTH_003",
                message="유효하지 않은 토큰입니다.",
                status_code=401,
            )

        user = self.repository.get_user_by_id(payload.subject)
        if user is None:
            raise AppError(
                code="E_RESOURCE_005",
                message="사용자를 찾을 수 없습니다",
                status_code=404,
            )

        self.repository.revoke_refresh_token(token_hash)
        return self._issue_tokens(user.id, user.role.value)

    def logout(self, *, refresh_token: str | None = None, user_id: str | None = None) -> None:
        if refresh_token:
            token_hash = hash_token(refresh_token)
            self.repository.revoke_refresh_token(token_hash)
            return

        if user_id is not None:
            self.repository.revoke_refresh_tokens_by_user_id(user_id)

    def _issue_tokens(self, user_id: str, role: str) -> AuthTokens:
        settings = get_settings()
        access = create_access_token(user_id, role)
        refresh, jti, expires_at = create_refresh_token(user_id)
        self.repository.create_refresh_token(
            user_id=user_id,
            token_hash=hash_token(refresh),
            jti=jti,
            expires_at=expires_at,
        )

        access_expires_in = settings.access_token_expire_minutes * 60
        access_expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        ).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        return AuthTokens(
            access_token=access,
            refresh_token=refresh,
            access_expires_in=access_expires_in,
            access_expires_at=access_expires_at,
        )
