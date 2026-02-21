# Authentication

## JWT 토큰 생성 (security.py)

```python
from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from trend_korea.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(dict):
    """JWT 디코딩 결과를 담는 페이로드"""

    @property
    def subject(self) -> str:
        return str(self.get("sub", ""))

    @property
    def jti(self) -> str:
        return str(self.get("jti", ""))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": expire, "type": "access"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """리프레시 토큰 생성. (token, jti, expires_at) 반환"""
    import uuid

    jti = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    token = jwt.encode(
        {"sub": user_id, "jti": jti, "exp": expires_at, "type": "refresh"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, jti, expires_at


def decode_token(token: str) -> TokenPayload:
    """토큰 디코딩. 실패 시 JWTError 또는 ExpiredSignatureError 발생"""
    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    return TokenPayload(payload)
```

## Header 기반 인증 (deps.py)

프로젝트는 `Authorization` 헤더에서 Bearer 토큰을 추출하는 방식을 사용한다.

```python
from typing import Annotated
from collections.abc import Generator

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from trend_korea.core.exceptions import AppError
from trend_korea.core.security import decode_token, TokenPayload
from trend_korea.core.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


DbSession = Annotated[Session, Depends(get_db_session)]


def get_current_user_id(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db_session),
) -> str:
    """Authorization 헤더에서 JWT를 검증하고 user_id를 반환"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(
            code="E_AUTH_001",
            message="인증 토큰이 필요합니다",
            status_code=401,
        )

    token = authorization.removeprefix("Bearer ")
    try:
        payload: TokenPayload = decode_token(token)
    except Exception:
        raise AppError(
            code="E_AUTH_002",
            message="유효하지 않은 토큰입니다",
            status_code=401,
        )

    user_id = payload.subject
    request.state.user_id = user_id
    request.state.user_role = payload.get("role")
    return user_id


# 타입 별칭: 인증된 사용자 ID
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
```

## 역할 기반 접근 제어

```python
def _require_member_or_admin(
    request: Request,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> str:
    """member 또는 admin 역할 필수"""
    role = getattr(request.state, "user_role", None)
    if role not in {"member", "admin"}:
        raise AppError(
            code="E_PERM_001",
            message="해당 기능에 대한 권한이 없습니다",
            status_code=403,
        )
    return user_id


def _require_admin(
    request: Request,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> str:
    """admin 역할 필수"""
    role = getattr(request.state, "user_role", None)
    if role != "admin":
        raise AppError(
            code="E_PERM_002",
            message="관리자 권한이 필요합니다",
            status_code=403,
        )
    return user_id


# 타입 별칭: 역할별 인증
CurrentMemberUserId = Annotated[str, Depends(_require_member_or_admin)]
CurrentAdminUserId = Annotated[str, Depends(_require_admin)]
```

## 라우터에서 사용

```python
from fastapi import APIRouter, Request

from trend_korea.core.deps import CurrentUserId, CurrentMemberUserId, CurrentAdminUserId, DbSession
from trend_korea.core.response import success_response

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="내 정보 조회")
def get_me(request: Request, user_id: CurrentUserId, db: DbSession):
    """인증된 사용자라면 누구나 접근 가능"""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    return success_response(request=request, data=user)


@router.patch("/me", summary="내 정보 수정")
def update_me(
    payload: UpdateProfileRequest,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    """member 또는 admin만 접근 가능"""
    repo = UserRepository(db)
    service = UserService(repo)
    user = service.update_profile(user_id, nickname=payload.nickname)
    db.commit()
    return success_response(request=request, data=user)


@router.delete("/{target_id}", summary="회원 삭제")
def delete_user(
    target_id: str,
    request: Request,
    admin_id: CurrentAdminUserId,
    db: DbSession,
):
    """admin만 접근 가능"""
    repo = UserRepository(db)
    repo.delete_by_id(target_id)
    db.commit()
    return success_response(request=request, message="삭제 완료")
```

## Refresh Token 갱신

```python
@router.post("/refresh", summary="토큰 갱신")
def refresh(payload: RefreshRequest, request: Request, db: DbSession):
    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception:
        raise AppError(code="E_AUTH_003", message="유효하지 않은 리프레시 토큰입니다", status_code=401)

    if token_payload.get("type") != "refresh":
        raise AppError(code="E_AUTH_004", message="잘못된 토큰 타입입니다", status_code=401)

    user_id = token_payload.subject
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise AppError(code="E_AUTH_005", message="사용자를 찾을 수 없습니다", status_code=401)

    access_token = create_access_token(user_id=user.id, role=user.role)
    refresh_token, jti, expires_at = create_refresh_token(user_id=user.id)
    db.commit()
    return success_response(
        request=request,
        data={"access_token": access_token, "refresh_token": refresh_token},
    )
```

## Quick Reference

| 컴포넌트 | 용도 |
|----------|------|
| `Header()` | Authorization 헤더에서 토큰 추출 |
| `decode_token()` | JWT 검증 및 디코딩 |
| `TokenPayload` | JWT 페이로드 (dict 서브클래스) |
| `create_access_token()` | 액세스 토큰 생성 |
| `create_refresh_token()` | 리프레시 토큰 생성 (token, jti, expires_at) |
| `pwd_context.hash()` | 비밀번호 해싱 |
| `pwd_context.verify()` | 비밀번호 검증 |
| `CurrentUserId` | 인증된 사용자 ID (역할 무관) |
| `CurrentMemberUserId` | member/admin 역할 필수 |
| `CurrentAdminUserId` | admin 역할 필수 |
| `AppError` | 인증/인가 에러 응답 |
