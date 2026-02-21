import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from src.core.config import get_settings
from src.core.exceptions import AppError


class TokenPayload(dict):
    @property
    def subject(self) -> str:
        return str(self.get("sub", ""))

    @property
    def jti(self) -> str:
        return str(self.get("jti", ""))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(user_id: str, role: str) -> str:
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "typ": "access",
        "exp": int(expire_at.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    jti = str(uuid4())
    expire_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "typ": "refresh",
        "jti": jti,
        "exp": int(expire_at.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire_at


def decode_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload(payload)
    except ExpiredSignatureError as exc:
        raise AppError(
            code="E_AUTH_002",
            message="인증 토큰이 만료되었습니다.",
            status_code=401,
        ) from exc
    except JWTError as exc:
        raise AppError(
            code="E_AUTH_003",
            message="유효하지 않은 토큰입니다.",
            status_code=401,
        ) from exc
