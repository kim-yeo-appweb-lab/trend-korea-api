from datetime import datetime

from trend_korea.domain.enums import TriggerType

from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentAdminUserId, CurrentMemberUserId, DbSession
from trend_korea.application.issues.service import IssueService
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.issue_repository import IssueRepository

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("")
def list_issues(
    request: Request,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None, pattern="^(ongoing|closed|reignited|unverified)$"),
    startDate: datetime | None = Query(default=None),
    endDate: datetime | None = Query(default=None),
    sortBy: str = Query(default="updatedAt"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    repository = IssueRepository(db)
    service = IssueService(repository)
    from trend_korea.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None
    sort = f"-{sortBy}" if order == "desc" else sortBy

    items, _ = service.list_issues(
        size=limit,
        cursor=cursor,
        sort=sort,
        status=status,
        from_at=startDate,
        to_at=endDate,
    )

    total_items = repository.count_issues(status=status, from_at=startDate, to_at=endDate)
    total_pages = (total_items + limit - 1) // limit if total_items else 0
    return success_response(
        request=request,
        data={
            "items": items,
            "pagination": {
                "currentPage": page,
                "totalPages": total_pages,
                "totalItems": total_items,
                "itemsPerPage": limit,
                "hasNext": page < total_pages,
                "hasPrev": page > 1,
            },
        },
        message="조회 성공",
    )


@router.get("/{issue_id}")
def get_issue(issue_id: str, request: Request, db: DbSession):
    service = IssueService(IssueRepository(db))
    item = service.get_issue(issue_id)
    if item is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)
    return success_response(request=request, data=item, message="조회 성공")


@router.post("")
def create_issue(payload: dict, request: Request, db: DbSession, _: CurrentAdminUserId):
    title = payload.get("title")
    description = payload.get("description")
    status = payload.get("status")
    tag_ids = payload.get("tagIds")
    source_ids = payload.get("sourceIds")
    related_event_ids = payload.get("relatedEventIds") or []

    if not isinstance(related_event_ids, list):
        raise AppError(code="E_VALID_002", message="relatedEventIds 형식이 올바르지 않습니다.", status_code=400)

    if not title or not description or not status:
        raise AppError(code="E_VALID_001", message="필수 필드가 누락되었습니다.", status_code=400)
    if not isinstance(tag_ids, list) or len(tag_ids) > 3:
        raise AppError(code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400)
    if not isinstance(source_ids, list) or len(source_ids) < 1:
        raise AppError(code="E_VALID_002", message="sourceIds는 최소 1개 필요합니다.", status_code=400)
    if status not in {"ongoing", "closed", "reignited", "unverified"}:
        raise AppError(code="E_VALID_002", message="status 값이 올바르지 않습니다.", status_code=400)

    service = IssueService(IssueRepository(db))
    created = service.create_issue(
        title=title,
        description=description,
        status=status,
        tag_ids=tag_ids,
        source_ids=source_ids,
        related_event_ids=related_event_ids,
    )
    db.commit()
    return success_response(request=request, data=created, status_code=201, message="이슈 생성 성공")


@router.patch("/{issue_id}")
def update_issue(issue_id: str, payload: dict, request: Request, db: DbSession, _: CurrentAdminUserId):
    status = payload.get("status")
    tag_ids = payload.get("tagIds")
    source_ids = payload.get("sourceIds")
    related_event_ids = payload.get("relatedEventIds")

    if related_event_ids is not None and not isinstance(related_event_ids, list):
        raise AppError(code="E_VALID_002", message="relatedEventIds 형식이 올바르지 않습니다.", status_code=400)
    if status is not None and status not in {"ongoing", "closed", "reignited", "unverified"}:
        raise AppError(code="E_VALID_002", message="status 값이 올바르지 않습니다.", status_code=400)
    if tag_ids is not None and (not isinstance(tag_ids, list) or len(tag_ids) > 3):
        raise AppError(code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400)
    if source_ids is not None and (not isinstance(source_ids, list) or len(source_ids) < 1):
        raise AppError(code="E_VALID_002", message="sourceIds는 최소 1개 필요합니다.", status_code=400)

    service = IssueService(IssueRepository(db))
    updated = service.update_issue(
        issue_id=issue_id,
        title=payload.get("title"),
        description=payload.get("description"),
        status=status,
        tag_ids=tag_ids,
        source_ids=source_ids,
        related_event_ids=related_event_ids,
    )
    if updated is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)

    db.commit()
    return success_response(
        request=request,
        data={
            "id": updated["id"],
            "title": updated["title"],
            "status": updated["status"],
            "updatedAt": updated["updatedAt"],
        },
        message="이슈 수정 성공",
    )


@router.delete("/{issue_id}")
def delete_issue(issue_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    service = IssueService(IssueRepository(db))
    ok = service.delete_issue(issue_id=issue_id)
    if not ok:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=None, message="이슈 삭제 성공")


@router.get("/{issue_id}/triggers")
def list_triggers(
    issue_id: str,
    request: Request,
    db: DbSession,
    sortBy: str = Query(default="occurredAt"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    _ = sortBy
    _ = order
    service = IssueService(IssueRepository(db))
    items, _ = service.list_triggers(issue_id=issue_id, size=100, cursor=None)
    return success_response(
        request=request,
        data=items,
        message="조회 성공",
    )


@router.post("/{issue_id}/track")
def track_issue(issue_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = IssueService(IssueRepository(db))
    if service.get_issue(issue_id) is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)
    tracked, tracked_at = service.track_issue(user_id=user_id, issue_id=issue_id)
    if not tracked:
        raise AppError(code="E_CONFLICT_002", message="이미 추적 중인 이슈입니다.", status_code=409)
    db.commit()
    return success_response(
        request=request,
        data={
            "issueId": issue_id,
            "isTracking": tracked,
            "trackedAt": tracked_at,
        },
        message="이슈 추적 시작",
    )


@router.delete("/{issue_id}/track")
def untrack_issue(issue_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = IssueService(IssueRepository(db))
    if service.get_issue(issue_id) is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)
    service.untrack_issue(user_id=user_id, issue_id=issue_id)
    db.commit()
    return success_response(request=request, data=None, message="이슈 추적 해제 완료")


@router.post("/{issue_id}/triggers")
def create_trigger(
    issue_id: str,
    payload: dict,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    occurred_at_raw = payload.get("occurredAt")
    summary = payload.get("summary")
    trigger_type = payload.get("type")
    source_ids = payload.get("sourceIds")

    if not occurred_at_raw or not summary or not trigger_type:
        raise AppError(code="E_VALID_001", message="필수 필드가 누락되었습니다.", status_code=400)
    if not isinstance(source_ids, list) or len(source_ids) < 1:
        raise AppError(code="E_VALID_002", message="sourceIds는 최소 1개 필요합니다.", status_code=400)

    try:
        TriggerType(trigger_type)
    except ValueError as exc:
        raise AppError(code="E_VALID_002", message="type 값이 올바르지 않습니다.", status_code=400) from exc

    try:
        occurred_at = datetime.fromisoformat(str(occurred_at_raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise AppError(code="E_VALID_002", message="occurredAt 형식이 올바르지 않습니다.", status_code=400) from exc

    service = IssueService(IssueRepository(db))
    created = service.create_trigger(
        issue_id=issue_id,
        occurred_at=occurred_at,
        summary=summary,
        trigger_type=trigger_type,
        source_ids=source_ids,
    )
    if created is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)

    db.commit()
    return success_response(request=request, data=created, status_code=201, message="트리거 생성 성공")
