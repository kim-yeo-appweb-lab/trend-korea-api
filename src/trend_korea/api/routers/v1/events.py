from datetime import datetime

from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentAdminUserId, CurrentMemberUserId, DbSession
from trend_korea.application.events.service import EventService
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.event_repository import EventRepository

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def list_events(
    request: Request,
    db: DbSession,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    importance: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    startDate: datetime | None = Query(default=None),
    endDate: datetime | None = Query(default=None),
    sortBy: str = Query(default="occurredAt"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
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


@router.get("/{event_id}")
def get_event(event_id: str, request: Request, db: DbSession):
    service = EventService(EventRepository(db))
    item = service.get_event(event_id)
    if item is None:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)
    return success_response(request=request, data=item, message="조회 성공")


@router.post("/{event_id}/save")
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


@router.delete("/{event_id}/save")
def unsave_event(event_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = EventService(EventRepository(db))
    if service.get_event(event_id) is None:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)
    service.unsave_event(user_id=user_id, event_id=event_id)
    db.commit()
    return success_response(request=request, data=None, message="사건 저장 해제 완료")


@router.post("")
def create_event(payload: dict, request: Request, db: DbSession, _: CurrentAdminUserId):
    occurred_at_raw = payload.get("occurredAt")
    title = payload.get("title")
    summary = payload.get("summary")
    importance = payload.get("importance")
    verification_status = payload.get("verificationStatus")
    tag_ids = payload.get("tagIds")
    source_ids = payload.get("sourceIds")

    if not occurred_at_raw or not title or not summary or not importance or not verification_status:
        raise AppError(code="E_VALID_001", message="필수 필드가 누락되었습니다.", status_code=400)
    if not isinstance(tag_ids, list) or len(tag_ids) > 3:
        raise AppError(code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400)
    if not isinstance(source_ids, list) or len(source_ids) < 1:
        raise AppError(code="E_VALID_002", message="sourceIds는 최소 1개 필요합니다.", status_code=400)
    if importance not in {"high", "medium", "low"}:
        raise AppError(code="E_VALID_002", message="importance 값이 올바르지 않습니다.", status_code=400)
    if verification_status not in {"verified", "unverified"}:
        raise AppError(code="E_VALID_002", message="verificationStatus 값이 올바르지 않습니다.", status_code=400)

    try:
        occurred_at = datetime.fromisoformat(str(occurred_at_raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise AppError(code="E_VALID_002", message="occurredAt 형식이 올바르지 않습니다.", status_code=400) from exc

    service = EventService(EventRepository(db))
    created = service.create_event(
        occurred_at=occurred_at,
        title=title,
        summary=summary,
        importance=importance,
        verification_status=verification_status,
        tag_ids=tag_ids,
        source_ids=source_ids,
    )

    db.commit()
    return success_response(request=request, data=created, status_code=201, message="사건 생성 성공")


@router.patch("/{event_id}")
def update_event(event_id: str, payload: dict, request: Request, db: DbSession, _: CurrentAdminUserId):
    service = EventService(EventRepository(db))
    tag_ids = payload.get("tagIds")
    source_ids = payload.get("sourceIds")

    if tag_ids is not None and (not isinstance(tag_ids, list) or len(tag_ids) > 3):
        raise AppError(code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400)
    if source_ids is not None and (not isinstance(source_ids, list) or len(source_ids) < 1):
        raise AppError(code="E_VALID_002", message="sourceIds는 최소 1개 필요합니다.", status_code=400)
    if payload.get("importance") is not None and payload.get("importance") not in {"high", "medium", "low"}:
        raise AppError(code="E_VALID_002", message="importance 값이 올바르지 않습니다.", status_code=400)
    if (
        payload.get("verificationStatus") is not None
        and payload.get("verificationStatus") not in {"verified", "unverified"}
    ):
        raise AppError(code="E_VALID_002", message="verificationStatus 값이 올바르지 않습니다.", status_code=400)

    updated = service.update_event(
        event_id=event_id,
        title=payload.get("title"),
        summary=payload.get("summary"),
        importance=payload.get("importance"),
        verification_status=payload.get("verificationStatus"),
        tag_ids=tag_ids,
        source_ids=source_ids,
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


@router.delete("/{event_id}")
def delete_event(event_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    service = EventService(EventRepository(db))
    ok = service.delete_event(event_id=event_id)
    if not ok:
        raise AppError(code="E_RESOURCE_001", message="사건을 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=None, message="사건 삭제 성공")
