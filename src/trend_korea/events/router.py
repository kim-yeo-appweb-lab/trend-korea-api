from datetime import datetime

from fastapi import APIRouter, Query, Request

from trend_korea.shared.dependencies import CurrentAdminUserId, CurrentMemberUserId, DbSession
from trend_korea.shared.schemas import ErrorResponse, RESPONSE_400, RESPONSE_401, RESPONSE_403_ADMIN
from trend_korea.events.schemas import CreateEventRequest, UpdateEventRequest
from trend_korea.events.service import EventService
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.events.repository import EventRepository

router = APIRouter(prefix="/events", tags=["events"])


@router.get(
    "",
    summary="사건 목록 조회",
    description="커서 기반 페이지네이션으로 사건 목록을 조회합니다. 중요도, 날짜 범위로 필터링하고 정렬 기준을 지정할 수 있습니다.",
)
def list_events(
    request: Request,
    db: DbSession,
    cursor: str | None = Query(default=None, description="다음 페이지 커서 토큰"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 항목 수"),
    importance: str | None = Query(default=None, pattern="^(low|medium|high)$", description="중요도 필터 (low, medium, high)"),
    startDate: datetime | None = Query(default=None, description="조회 시작 날짜 (ISO 8601)"),
    endDate: datetime | None = Query(default=None, description="조회 종료 날짜 (ISO 8601)"),
    sortBy: str = Query(default="occurredAt", description="정렬 기준 필드 (occurredAt, createdAt)"),
    order: str = Query(default="desc", pattern="^(asc|desc)$", description="정렬 방향 (asc, desc)"),
):
    service = EventService(EventRepository(db))
    sort = f"-{sortBy}" if order == "desc" else sortBy
    items, next_cursor = service.list_events(
        size=limit,
        cursor=cursor,
        sort=sort,
        importance=importance,
        verification_status=None,
        from_at=startDate,
        to_at=endDate,
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


@router.get(
    "/{event_id}",
    summary="사건 상세 조회",
    description="사건 ID로 상세 정보를 조회합니다. 연관 태그, 출처 정보를 포함합니다.",
    responses={
        404: {
            "description": "사건을 찾을 수 없음 (`E_RESOURCE_001`)",
            "model": ErrorResponse,
        },
    },
)
def get_event(event_id: str, request: Request, db: DbSession):
    service = EventService(EventRepository(db))
    item = service.get_event(event_id)
    if item is None:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)
    return success_response(request=request, data=item, message="조회 성공")


@router.post(
    "/{event_id}/save",
    summary="사건 저장",
    description="사건을 내 저장 목록에 추가합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        404: {"description": "사건을 찾을 수 없음 (`E_RESOURCE_001`)", "model": ErrorResponse},
        409: {"description": "이미 저장된 사건 (`E_CONFLICT_003`)", "model": ErrorResponse},
    },
)
def save_event(event_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = EventService(EventRepository(db))
    if service.get_event(event_id) is None:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)
    saved, saved_at = service.save_event(user_id=user_id, event_id=event_id)
    if not saved:
        raise AppError(code="E_CONFLICT_003", message="이미 저장된 사건입니다.", status_code=409)
    db.commit()
    return success_response(
        request=request,
        data={
            "eventId": event_id,
            "isSaved": saved,
            "savedAt": saved_at,
        },
        message="사건 저장 성공",
    )


@router.delete(
    "/{event_id}/save",
    summary="사건 저장 해제",
    description="저장된 사건을 내 저장 목록에서 제거합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        404: {"description": "사건을 찾을 수 없음 (`E_RESOURCE_001`)", "model": ErrorResponse},
    },
)
def unsave_event(event_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = EventService(EventRepository(db))
    if service.get_event(event_id) is None:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)
    service.unsave_event(user_id=user_id, event_id=event_id)
    db.commit()
    return success_response(request=request, data=None, message="사건 저장 해제 완료")


@router.post(
    "",
    summary="사건 생성 (관리자)",
    description="새 사건을 등록합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    status_code=201,
    responses={**RESPONSE_400, **RESPONSE_401, **RESPONSE_403_ADMIN},
)
def create_event(payload: CreateEventRequest, request: Request, db: DbSession, _: CurrentAdminUserId):
    service = EventService(EventRepository(db))
    created = service.create_event(
        occurred_at=payload.occurredAt,
        title=payload.title,
        summary=payload.summary,
        importance=payload.importance.value,
        verification_status=payload.verificationStatus.value,
        tag_ids=payload.tagIds,
        source_ids=payload.sourceIds,
    )

    db.commit()
    return success_response(request=request, data=created, status_code=201, message="사건 생성 성공")


@router.patch(
    "/{event_id}",
    summary="사건 수정 (관리자)",
    description="사건 정보를 수정합니다. 변경할 필드만 전송합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "사건을 찾을 수 없음 (`E_RESOURCE_001`)", "model": ErrorResponse},
    },
)
def update_event(event_id: str, payload: UpdateEventRequest, request: Request, db: DbSession, _: CurrentAdminUserId):
    service = EventService(EventRepository(db))

    updated = service.update_event(
        event_id=event_id,
        title=payload.title,
        summary=payload.summary,
        importance=payload.importance.value if payload.importance is not None else None,
        verification_status=payload.verificationStatus.value if payload.verificationStatus is not None else None,
        tag_ids=payload.tagIds,
        source_ids=payload.sourceIds,
    )
    if updated is None:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)

    db.commit()
    return success_response(
        request=request,
        data={
            "id": updated["id"],
            "title": updated["title"],
            "importance": updated["importance"],
            "updatedAt": updated["updatedAt"],
        },
        message="사건 수정 성공",
    )


@router.delete(
    "/{event_id}",
    summary="사건 삭제 (관리자)",
    description="사건을 삭제합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "사건을 찾을 수 없음 (`E_RESOURCE_001`)", "model": ErrorResponse},
    },
)
def delete_event(event_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    service = EventService(EventRepository(db))
    ok = service.delete_event(event_id=event_id)
    if not ok:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=None, message="사건 삭제 성공")
