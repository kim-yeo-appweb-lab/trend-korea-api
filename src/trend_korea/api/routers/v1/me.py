from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentMemberUserId, DbSession
from trend_korea.api.schemas.common import ErrorResponse, RESPONSE_400, RESPONSE_401
from trend_korea.api.schemas.me import ChangePasswordRequest, SocialConnectRequest, SocialDisconnectRequest, UpdateMeRequest
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.core.security import hash_password, verify_password
from trend_korea.infrastructure.db.repositories.auth_repository import AuthRepository
from trend_korea.infrastructure.db.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users/me", tags=["users"])

def _to_iso(dt):
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


@router.get(
    "",
    summary="내 정보 조회",
    description="현재 로그인된 사용자의 프로필 정보를 반환합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_401},
)
def get_me(request: Request, user_id: CurrentMemberUserId, db: DbSession):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise AppError(code="E_RESOURCE_005", message="사용자를 찾을 수 없습니다", status_code=404)

    return success_response(
        request=request,
        data={
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "profileImage": user.profile_image,
            "role": user.role.value,
            "socialProviders": [],
            "trackedIssueIds": [],
            "savedEventIds": [],
            "createdAt": _to_iso(user.created_at),
            "updatedAt": _to_iso(user.updated_at),
        },
        message="조회 성공",
    )


@router.patch(
    "",
    summary="내 정보 수정",
    description="닉네임, 프로필 이미지 등 내 정보를 수정합니다. 변경할 필드만 전송합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        409: {
            "description": "이미 사용 중인 닉네임 (`E_CONFLICT_002`)",
            "model": ErrorResponse,
        },
    },
)
def update_me(payload: UpdateMeRequest, request: Request, user_id: CurrentMemberUserId, db: DbSession):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise AppError(code="E_RESOURCE_005", message="사용자를 찾을 수 없습니다", status_code=404)

    if payload.nickname and payload.nickname != user.nickname:
        nickname_taken = repo.get_by_nickname(payload.nickname)
        if nickname_taken is not None and nickname_taken.id != user.id:
            raise AppError(
                code="E_CONFLICT_002",
                message="이미 사용 중인 닉네임입니다.",
                status_code=409,
                details={"field": "nickname"},
            )

    updated = repo.update_profile(
        user,
        nickname=payload.nickname,
        profile_image=payload.profileImage,
    )
    db.commit()
    return success_response(
        request=request,
        data={
            "id": updated.id,
            "nickname": updated.nickname,
            "profileImage": updated.profile_image,
            "updatedAt": _to_iso(updated.updated_at),
        },
        message="정보 수정 성공",
    )


@router.post(
    "/change-password",
    summary="비밀번호 변경",
    description="현재 비밀번호를 확인한 후 새 비밀번호로 변경합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        401: {
            "description": "현재 비밀번호 불일치 (`E_AUTH_001`)",
            "model": ErrorResponse,
        },
    },
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    auth_repo = AuthRepository(db)
    user = auth_repo.get_user_by_id(user_id)
    if user is None:
        raise AppError(code="E_RESOURCE_005", message="사용자를 찾을 수 없습니다", status_code=404)

    if not verify_password(payload.currentPassword, user.password_hash):
        raise AppError(code="E_AUTH_001", message="현재 비밀번호가 일치하지 않습니다.", status_code=401)

    user.password_hash = hash_password(payload.newPassword)
    db.flush()
    db.commit()

    return success_response(
        request=request,
        data=None,
        message="비밀번호 변경 성공",
    )


@router.post(
    "/social-connect",
    summary="SNS 계정 연동",
    description="현재 계정에 SNS 계정을 연동합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_400, **RESPONSE_401},
)
def social_connect(
    payload: SocialConnectRequest,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    _ = db
    _ = user_id
    return success_response(
        request=request,
        data={"socialProviders": [payload.provider]},
        message="SNS 연동 성공",
    )


@router.delete(
    "/social-disconnect",
    summary="SNS 계정 연동 해제",
    description="연동된 SNS 계정을 해제합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_400, **RESPONSE_401},
)
def social_disconnect(
    payload: SocialDisconnectRequest,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    _ = db
    _ = user_id
    return success_response(
        request=request,
        data={"socialProviders": []},
        message="SNS 연동 해제 완료",
    )


@router.get(
    "/activity",
    summary="내 활동 내역 조회",
    description="게시글, 댓글, 추천 등 내 활동 내역을 페이지네이션으로 조회합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_401},
)
def get_my_activity(
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="페이지당 항목 수"),
    type: str = Query(default="all", description="활동 유형 필터 (all, post, comment, like)"),
):
    _ = user_id
    _ = db
    return success_response(
        request=request,
        data={
            "items": [],
            "pagination": {
                "currentPage": page,
                "totalPages": 0,
                "totalItems": 0,
                "itemsPerPage": limit,
                "hasNext": False,
                "hasPrev": page > 1,
            },
        },
        message="조회 성공",
    )
