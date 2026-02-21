from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentMemberUserId, DbSession
from trend_korea.api.schemas.common import RESPONSE_401
from trend_korea.application.events.service import EventService
from trend_korea.application.issues.service import IssueService
from trend_korea.application.tracking.service import TrackingService
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.event_repository import EventRepository
from trend_korea.infrastructure.db.repositories.issue_repository import IssueRepository

router = APIRouter(prefix="/users/me", tags=["tracking"])


@router.get(
    "/tracked-issues",
    summary="추적 중인 이슈 목록",
    description="내가 추적 중인 이슈 목록을 페이지 기반 페이지네이션으로 조회합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_401},
)
def tracked_issues(
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 항목 수"),
    sortBy: str = Query(default="trackedAt", description="정렬 기준 필드 (trackedAt, latestTriggerAt)"),
):
    issue_repository = IssueRepository(db)
    service = TrackingService(
        issue_service=IssueService(issue_repository),
        event_service=EventService(EventRepository(db)),
    )
    offset = (page - 1) * limit
    cursor = ""
    if offset > 0:
        from trend_korea.core.pagination import encode_cursor

        cursor = encode_cursor(offset)

    sort = f"-{sortBy}"
    items, _ = service.tracked_issues(user_id=user_id, size=limit, cursor=cursor or None, sort=sort)

    total_items = issue_repository.count_tracked_issues(user_id=user_id)
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


@router.get(
    "/saved-events",
    summary="저장한 사건 목록",
    description="내가 저장한 사건 목록을 페이지 기반 페이지네이션으로 조회합니다. `Authorization: Bearer <token>` 필요.",
    responses={**RESPONSE_401},
)
def saved_events(
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 항목 수"),
    sortBy: str = Query(default="savedAt", description="정렬 기준 필드 (savedAt, occurredAt)"),
):
    event_repository = EventRepository(db)
    service = TrackingService(
        issue_service=IssueService(IssueRepository(db)),
        event_service=EventService(event_repository),
    )
    offset = (page - 1) * limit
    cursor = ""
    if offset > 0:
        from trend_korea.core.pagination import encode_cursor

        cursor = encode_cursor(offset)

    sort = "-occurredAt" if sortBy == "savedAt" else f"-{sortBy}"
    items, _ = service.saved_events(user_id=user_id, size=limit, cursor=cursor or None, sort=sort)

    total_items = event_repository.count_saved_events(user_id=user_id)
    total_pages = (total_items + limit - 1) // limit if total_items else 0
    return success_response(
        request=request,
        data={
            "items": [
                {
                    "id": item["id"],
                    "occurredAt": item["occurredAt"],
                    "title": item["title"],
                    "importance": item["importance"],
                    "tags": item.get("tags", []),
                    "savedAt": item.get("savedAt"),
                }
                for item in items
            ],
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
