from fastapi import APIRouter, Query, Request

from src.utils.dependencies import CurrentMemberUserId, DbSession
from src.schemas.shared import ErrorResponse, RESPONSE_400, RESPONSE_401
from src.schemas.users import (
    ChangePasswordRequest,
    SocialConnectRequest,
    SocialDisconnectRequest,
    UpdateMeRequest,
)
from src.schemas.notification import CreateAlertRuleRequest
from src.schemas.subscription import CreateSubscriptionRequest
from src.core.exceptions import AppError
from src.core.response import success_response
from src.core.security import hash_password, verify_password
from src.crud.notification import NotificationService
from src.crud.subscription import SubscriptionService
from src.sql.auth import AuthRepository
from src.sql.notification import NotificationRepository
from src.sql.subscription import SubscriptionRepository
from src.sql.users import UserRepository

me_router = APIRouter(prefix="/users/me", tags=["users"])


def _to_iso(dt):
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


@me_router.get(
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


@me_router.patch(
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
def update_me(
    payload: UpdateMeRequest, request: Request, user_id: CurrentMemberUserId, db: DbSession
):
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


@me_router.post(
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
        raise AppError(
            code="E_AUTH_001", message="현재 비밀번호가 일치하지 않습니다.", status_code=401
        )

    user.password_hash = hash_password(payload.newPassword)
    db.flush()
    db.commit()

    return success_response(
        request=request,
        data=None,
        message="비밀번호 변경 성공",
    )


@me_router.post(
    "/social-connect",
    summary="SNS 계정 연동 (미구현)",
    description="현재 계정에 SNS 계정을 연동합니다. (미구현) `Authorization: Bearer <token>` 필요.",
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


@me_router.delete(
    "/social-disconnect",
    summary="SNS 계정 연동 해제 (미구현)",
    description="연동된 SNS 계정을 해제합니다. (미구현) `Authorization: Bearer <token>` 필요.",
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


@me_router.get(
    "/activity",
    summary="내 활동 내역 조회 (미구현)",
    description="게시글, 댓글, 추천 등 내 활동 내역을 페이지네이션으로 조회합니다. (미구현) `Authorization: Bearer <token>` 필요.",
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


# ── 알림 규칙 ──


@me_router.post(
    "/alert-rules",
    summary="알림 규칙 생성",
    description="키워드 또는 중요도 기반 알림 규칙을 생성합니다.",
    responses={**RESPONSE_401},
)
def create_alert_rule(
    payload: CreateAlertRuleRequest,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = NotificationService(NotificationRepository(db))
    rule = service.create_alert_rule(
        user_id=user_id,
        keyword=payload.keyword,
        min_importance=payload.minImportance,
    )
    db.commit()
    return success_response(
        request=request,
        data=rule,
        status_code=201,
        message="알림 규칙 생성 성공",
    )


@me_router.get(
    "/alert-rules",
    summary="알림 규칙 목록",
    description="내 알림 규칙 목록을 조회합니다.",
    responses={**RESPONSE_401},
)
def list_alert_rules(
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = NotificationService(NotificationRepository(db))
    rules = service.list_alert_rules(user_id=user_id)
    return success_response(request=request, data=rules, message="조회 성공")


@me_router.delete(
    "/alert-rules/{rule_id}",
    summary="알림 규칙 삭제",
    description="알림 규칙을 삭제합니다.",
    responses={**RESPONSE_401},
)
def delete_alert_rule(
    rule_id: str,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = NotificationService(NotificationRepository(db))
    deleted = service.delete_alert_rule(rule_id=rule_id, user_id=user_id)
    if not deleted:
        raise AppError(
            code="E_RESOURCE_008",
            message="알림 규칙을 찾을 수 없습니다",
            status_code=404,
        )
    db.commit()
    return success_response(request=request, data=None, message="알림 규칙 삭제 성공")


# ── 알림 ──


@me_router.get(
    "/notifications",
    summary="알림 목록 조회",
    description="내 알림 목록을 커서 기반으로 조회합니다.",
    responses={**RESPONSE_401},
)
def list_notifications(
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
    cursor: str | None = Query(default=None, description="다음 페이지 커서"),
    limit: int = Query(default=20, ge=1, le=100, description="한 번에 조회할 항목 수"),
):
    service = NotificationService(NotificationRepository(db))
    items, next_cursor = service.list_notifications(
        user_id=user_id,
        cursor=cursor,
        size=limit,
    )
    return success_response(
        request=request,
        data={
            "items": items,
            "cursor": {
                "next": next_cursor,
                "hasMore": next_cursor is not None,
            },
        },
        message="조회 성공",
    )


@me_router.patch(
    "/notifications/{notification_id}/read",
    summary="알림 읽음 처리",
    description="특정 알림을 읽음 처리합니다.",
    responses={**RESPONSE_401},
)
def mark_notification_read(
    notification_id: str,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = NotificationService(NotificationRepository(db))
    result = service.mark_read(notification_id=notification_id, user_id=user_id)
    if result is None:
        raise AppError(
            code="E_RESOURCE_009",
            message="알림을 찾을 수 없습니다",
            status_code=404,
        )
    db.commit()
    return success_response(request=request, data=result, message="읽음 처리 성공")


@me_router.post(
    "/notifications/read-all",
    summary="전체 알림 읽음 처리",
    description="읽지 않은 모든 알림을 읽음 처리합니다.",
    responses={**RESPONSE_401},
)
def mark_all_notifications_read(
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = NotificationService(NotificationRepository(db))
    count = service.mark_all_read(user_id=user_id)
    db.commit()
    return success_response(
        request=request,
        data={"updatedCount": count},
        message="전체 읽음 처리 성공",
    )


# ── 키워드 구독 ──


@me_router.post(
    "/subscriptions",
    summary="키워드 구독",
    description="키워드를 구독하여 관련 기사가 수집되면 알림을 받습니다.",
    responses={**RESPONSE_401},
)
def create_subscription(
    payload: CreateSubscriptionRequest,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = SubscriptionService(SubscriptionRepository(db))
    try:
        sub = service.create_subscription(user_id=user_id, keyword=payload.keyword)
    except Exception:
        raise AppError(
            code="E_CONFLICT_003",
            message="이미 구독 중인 키워드입니다",
            status_code=409,
        )
    db.commit()
    return success_response(
        request=request,
        data=sub,
        status_code=201,
        message="키워드 구독 성공",
    )


@me_router.get(
    "/subscriptions",
    summary="구독 목록",
    description="내 키워드 구독 목록을 조회합니다.",
    responses={**RESPONSE_401},
)
def list_subscriptions(
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = SubscriptionService(SubscriptionRepository(db))
    subs = service.list_subscriptions(user_id=user_id)
    return success_response(request=request, data=subs, message="조회 성공")


@me_router.delete(
    "/subscriptions/{subscription_id}",
    summary="구독 해제",
    description="키워드 구독을 해제합니다.",
    responses={**RESPONSE_401},
)
def delete_subscription(
    subscription_id: str,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
):
    service = SubscriptionService(SubscriptionRepository(db))
    deleted = service.delete_subscription(
        subscription_id=subscription_id,
        user_id=user_id,
    )
    if not deleted:
        raise AppError(
            code="E_RESOURCE_010",
            message="구독을 찾을 수 없습니다",
            status_code=404,
        )
    db.commit()
    return success_response(request=request, data=None, message="구독 해제 성공")


@me_router.get(
    "/subscriptions/{subscription_id}/matches",
    summary="매칭 기사 목록",
    description="구독 키워드와 매칭된 기사 목록을 조회합니다.",
    responses={**RESPONSE_401},
)
def list_subscription_matches(
    subscription_id: str,
    request: Request,
    user_id: CurrentMemberUserId,
    db: DbSession,
    cursor: str | None = Query(default=None, description="다음 페이지 커서"),
    limit: int = Query(default=20, ge=1, le=100, description="한 번에 조회할 항목 수"),
):
    service = SubscriptionService(SubscriptionRepository(db))
    result = service.list_matches(
        subscription_id=subscription_id,
        user_id=user_id,
        cursor=cursor,
        size=limit,
    )
    if result is None:
        raise AppError(
            code="E_RESOURCE_010",
            message="구독을 찾을 수 없습니다",
            status_code=404,
        )
    items, next_cursor = result
    return success_response(
        request=request,
        data={
            "items": items,
            "cursor": {
                "next": next_cursor,
                "hasMore": next_cursor is not None,
            },
        },
        message="조회 성공",
    )


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get(
    "/{user_id}",
    summary="사용자 공개 프로필 조회",
    description="사용자 ID로 공개 프로필 정보를 조회합니다. 닉네임, 프로필 이미지, 활동 통계를 포함합니다.",
    responses={
        404: {"description": "사용자를 찾을 수 없음 (`E_RESOURCE_005`)", "model": ErrorResponse},
    },
)
def get_user(user_id: str, request: Request, db: DbSession):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise AppError(code="E_RESOURCE_005", message="사용자를 찾을 수 없습니다", status_code=404)

    return success_response(
        request=request,
        data={
            "id": user.id,
            "nickname": user.nickname,
            "profileImage": user.profile_image,
            "bio": None,
            "createdAt": user.created_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "activityStats": {
                "postCount": 0,
                "commentCount": 0,
                "likeCount": 0,
            },
        },
        message="조회 성공",
    )
