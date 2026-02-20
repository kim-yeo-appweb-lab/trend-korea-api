from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from trend_korea.core.exceptions import AppError
from trend_korea.core.security import decode_token
from trend_korea.infrastructure.db.repositories.auth_repository import AuthRepository
from trend_korea.infrastructure.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


DbSession = Annotated[Session, Depends(get_db_session)]


def get_current_user_id(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db_session),
) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError(
            code="E_AUTH_001",
            message="인증 토큰이 없습니다",
            status_code=401,
        )

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if payload.get("typ") != "access":
        raise AppError(
            code="E_AUTH_003",
            message="유효하지 않은 토큰입니다.",
            status_code=401,
        )

    user_id = payload.subject
    if not user_id:
        raise AppError(
            code="E_AUTH_003",
            message="유효하지 않은 토큰입니다.",
            status_code=401,
        )

    repository = AuthRepository(db)
    user = repository.get_user_by_id(user_id)
    if user is None:
        raise AppError(
            code="E_RESOURCE_005",
            message="사용자를 찾을 수 없습니다",
            status_code=404,
        )

    request.state.user_id = user_id
    request.state.user_role = user.role.value
    return user_id


def _require_member_or_admin(
    request: Request,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> str:
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
    role = getattr(request.state, "user_role", None)
    if role != "admin":
        raise AppError(
            code="E_PERM_002",
            message="관리자 권한이 필요합니다",
            status_code=403,
        )
    return user_id


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentMemberUserId = Annotated[str, Depends(_require_member_or_admin)]
CurrentAdminUserId = Annotated[str, Depends(_require_admin)]
