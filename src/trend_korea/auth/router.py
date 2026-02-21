from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Request

from trend_korea.auth.repository import AuthRepository
from trend_korea.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SocialLoginRequest,
    WithdrawRequest,
)
from trend_korea.auth.service import AuthService
from trend_korea.core.response import success_response
from trend_korea.core.security import hash_password
from trend_korea.shared.dependencies import CurrentMemberUserId, DbSession
from trend_korea.shared.schemas import RESPONSE_400, RESPONSE_401, ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])

def _to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


@router.post(
    "/register",
    summary="회원가입",
    description="이메일/비밀번호로 새 계정을 생성합니다. 성공 시 사용자 정보와 토큰을 반환합니다.",
    status_code=201,
    responses={
        **RESPONSE_400,
        409: {
            "description": "이미 가입된 이메일 (`E_CONFLICT_001`)",
            "model": ErrorResponse,
        },
    },
)
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


@router.post(
    "/login",
    summary="로그인",
    description="이메일/비밀번호로 로그인합니다. 성공 시 사용자 정보와 액세스/리프레시 토큰을 반환합니다.",
    responses={
        **RESPONSE_400,
        401: {
            "description": "이메일 또는 비밀번호 불일치 (`E_AUTH_002`)",
            "model": ErrorResponse,
        },
    },
)
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


@router.post(
    "/refresh",
    summary="토큰 갱신",
    description="리프레시 토큰으로 새 액세스 토큰을 발급받습니다.",
    responses={
        **RESPONSE_400,
        401: {
            "description": "유효하지 않거나 만료된 리프레시 토큰 (`E_AUTH_003`)",
            "model": ErrorResponse,
        },
    },
)
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


@router.post(
    "/logout",
    summary="로그아웃",
    description="현재 사용자의 세션을 종료합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_401},
)
def logout(
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = AuthService(AuthRepository(db))
    service.logout(user_id=user_id)
    db.commit()
    return success_response(request=request, data=None, message="로그아웃 성공")


@router.get(
    "/social/providers",
    summary="SNS 로그인 제공자 목록",
    description="지원하는 SNS 로그인 제공자 목록을 반환합니다.",
)
def social_providers(request: Request):
    return success_response(
        request=request,
        data=["kakao", "naver", "google"],
        message="조회 성공",
    )


@router.post(
    "/social-login",
    summary="SNS 로그인",
    description="SNS OAuth 인가 코드로 로그인합니다. 미가입 사용자는 자동 회원가입 후 로그인됩니다.",
    responses={**RESPONSE_400},
)
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


@router.delete(
    "/withdraw",
    summary="회원탈퇴",
    description="계정을 삭제합니다. 이메일 가입 사용자는 비밀번호 확인이 필요합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_401},
)
def withdraw(
    payload: WithdrawRequest,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = AuthService(AuthRepository(db))
    service.withdraw(user_id=user_id, password=payload.password)
    db.commit()

    return success_response(
        request=request,
        data=None,
        message="회원탈퇴 완료",
    )
