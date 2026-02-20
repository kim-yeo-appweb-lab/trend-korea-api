from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Request

from trend_korea.api.deps import CurrentMemberUserId, DbSession
from trend_korea.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SocialLoginRequest,
    WithdrawRequest,
)
from trend_korea.application.auth.service import AuthService
from trend_korea.core.response import success_response
from trend_korea.core.security import hash_password
from trend_korea.infrastructure.db.repositories.auth_repository import AuthRepository

router = APIRouter(prefix="/auth", tags=["auth"])

def _to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


@router.post("/register")
def register(payload: RegisterRequest, request: Request, db: DbSession):
    service = AuthService(AuthRepository(db))
    tokens = service.register(
        nickname=payload.nickname,
        email=payload.email,
        password=payload.password,
    )
    user = service.repository.get_user_by_email(payload.email)
    db.commit()

    return success_response(
        request=request,
        data={
            "user": {
                "id": user.id if user else None,
                "email": payload.email,
                "nickname": payload.nickname,
                "role": "member",
                "createdAt": _to_iso(user.created_at) if user else None,
            },
            "tokens": {
                "accessToken": tokens.access_token,
                "refreshToken": tokens.refresh_token,
                "expiresIn": tokens.access_expires_in,
            },
        },
        message="회원가입 성공",
        status_code=201,
    )


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: DbSession):
    service = AuthService(AuthRepository(db))
    tokens = service.login(email=payload.email, password=payload.password)
    user = service.repository.get_user_by_email(payload.email)
    db.commit()

    return success_response(
        request=request,
        data={
            "user": {
                "id": user.id if user else None,
                "email": user.email if user else payload.email,
                "nickname": user.nickname if user else None,
                "profileImage": user.profile_image if user else None,
                "role": user.role.value if user else "member",
                "trackedIssueIds": [],
                "savedEventIds": [],
            },
            "tokens": {
                "accessToken": tokens.access_token,
                "refreshToken": tokens.refresh_token,
                "expiresIn": tokens.access_expires_in,
                "expiresAt": tokens.access_expires_at,
            },
        },
        message="로그인 성공",
    )


@router.post("/refresh")
def refresh(payload: RefreshRequest, request: Request, db: DbSession):
    service = AuthService(AuthRepository(db))
    tokens = service.refresh(refresh_token=payload.refreshToken)
    db.commit()

    return success_response(
        request=request,
        data={
            "accessToken": tokens.access_token,
            "expiresIn": tokens.access_expires_in,
            "expiresAt": tokens.access_expires_at,
        },
        message="토큰 갱신 성공",
    )


@router.post("/logout")
def logout(
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = AuthService(AuthRepository(db))
    service.logout(user_id=user_id)
    db.commit()
    return success_response(request=request, data=None, message="로그아웃 성공")


@router.get("/social/providers")
def social_providers(request: Request):
    return success_response(
        request=request,
        data=["kakao", "naver", "google"],
        message="조회 성공",
    )


@router.post("/social-login")
def social_login(payload: SocialLoginRequest, request: Request, db: DbSession):
    repository = AuthRepository(db)
    service = AuthService(repository)
    social_email = f"{payload.provider}_{payload.code[:12]}@social.trend-korea.local"
    user = repository.get_user_by_email(social_email)
    is_new_user = False
    if user is None:
        is_new_user = True
        user = repository.create_user(
            nickname=f"{payload.provider}_{uuid4().hex[:8]}",
            email=social_email,
            password_hash=hash_password(uuid4().hex),
        )
    tokens = service._issue_tokens(user.id, user.role.value)
    db.commit()

    return success_response(
        request=request,
        data={
            "user": {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role.value,
                "socialProviders": [payload.provider],
                "profileImage": user.profile_image,
            },
            "tokens": {
                "accessToken": tokens.access_token,
                "refreshToken": tokens.refresh_token,
                "expiresIn": tokens.access_expires_in,
            },
            "isNewUser": is_new_user,
        },
        message="SNS 로그인 성공",
    )


@router.delete("/withdraw")
def withdraw(
    payload: WithdrawRequest,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = AuthService(AuthRepository(db))
    service.logout(user_id=user_id)
    db.commit()

    return success_response(
        request=request,
        data=None,
        message="회원탈퇴 완료",
    )
