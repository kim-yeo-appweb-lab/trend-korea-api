from datetime import datetime

from fastapi import APIRouter, Query, Request

from src.utils.dependencies import CurrentAdminUserId, CurrentMemberUserId, DbSession
from src.schemas.shared import ErrorResponse, RESPONSE_400, RESPONSE_401, RESPONSE_403_ADMIN
from src.schemas.issues import CreateIssueRequest, CreateTriggerRequest, UpdateIssueRequest
from src.crud.issues import IssueService
from src.core.exceptions import AppError
from src.core.response import success_response
from src.sql.issues import IssueRepository

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get(
    "",
    summary="이슈 목록 조회",
    description="페이지 기반 페이지네이션으로 이슈 목록을 조회합니다. 상태, 날짜 범위로 필터링하고 정렬 기준을 지정할 수 있습니다.",
)
def list_issues(
    request: Request,
    db: DbSession,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 항목 수"),
    status: str | None = Query(
        default=None,
        pattern="^(ongoing|closed|reignited|unverified)$",
        description="이슈 상태 필터 (ongoing, closed, reignited, unverified)",
    ),
    startDate: datetime | None = Query(default=None, description="조회 시작 날짜 (ISO 8601)"),
    endDate: datetime | None = Query(default=None, description="조회 종료 날짜 (ISO 8601)"),
    sortBy: str = Query(
        default="updatedAt", description="정렬 기준 필드 (updatedAt, latestTriggerAt, createdAt)"
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$", description="정렬 방향 (asc, desc)"),
):
    repository = IssueRepository(db)
    service = IssueService(repository)
    from src.core.pagination import encode_cursor

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


@router.get(
    "/{issue_id}",
    summary="이슈 상세 조회",
    description="이슈 ID로 상세 정보를 조회합니다. 연관 태그, 출처, 트리거 정보를 포함합니다.",
    responses={
        404: {"description": "이슈를 찾을 수 없음 (`E_RESOURCE_002`)", "model": ErrorResponse},
    },
)
def get_issue(issue_id: str, request: Request, db: DbSession):
    service = IssueService(IssueRepository(db))
    item = service.get_issue(issue_id)
    if item is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)
    return success_response(request=request, data=item, message="조회 성공")


@router.post(
    "",
    summary="이슈 생성 (관리자)",
    description="새 이슈를 등록합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    status_code=201,
    responses={**RESPONSE_400, **RESPONSE_401, **RESPONSE_403_ADMIN},
)
def create_issue(
    payload: CreateIssueRequest, request: Request, db: DbSession, _: CurrentAdminUserId
):
    service = IssueService(IssueRepository(db))
    created = service.create_issue(
        title=payload.title,
        description=payload.description,
        status=payload.status.value,
        tag_ids=payload.tagIds,
        source_ids=payload.sourceIds,
        related_event_ids=payload.relatedEventIds,
    )
    db.commit()
    return success_response(
        request=request, data=created, status_code=201, message="이슈 생성 성공"
    )


@router.patch(
    "/{issue_id}",
    summary="이슈 수정 (관리자)",
    description="이슈 정보를 수정합니다. 변경할 필드만 전송합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "이슈를 찾을 수 없음 (`E_RESOURCE_002`)", "model": ErrorResponse},
    },
)
def update_issue(
    issue_id: str,
    payload: UpdateIssueRequest,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    service = IssueService(IssueRepository(db))
    updated = service.update_issue(
        issue_id=issue_id,
        title=payload.title,
        description=payload.description,
        status=payload.status.value if payload.status is not None else None,
        tag_ids=payload.tagIds,
        source_ids=payload.sourceIds,
        related_event_ids=payload.relatedEventIds,
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


@router.delete(
    "/{issue_id}",
    summary="이슈 삭제 (관리자)",
    description="이슈를 삭제합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "이슈를 찾을 수 없음 (`E_RESOURCE_002`)", "model": ErrorResponse},
    },
)
def delete_issue(issue_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    service = IssueService(IssueRepository(db))
    ok = service.delete_issue(issue_id=issue_id)
    if not ok:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=None, message="이슈 삭제 성공")


@router.get(
    "/{issue_id}/triggers",
    summary="이슈 트리거 목록 조회",
    description="특정 이슈에 등록된 트리거(사건 경과) 목록을 조회합니다.",
    responses={
        404: {"description": "이슈를 찾을 수 없음 (`E_RESOURCE_002`)", "model": ErrorResponse},
    },
)
def list_triggers(
    issue_id: str,
    request: Request,
    db: DbSession,
    sortBy: str = Query(default="occurredAt", description="정렬 기준 필드"),
    order: str = Query(default="desc", pattern="^(asc|desc)$", description="정렬 방향 (asc, desc)"),
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


@router.post(
    "/{issue_id}/track",
    summary="이슈 추적 시작",
    description="이슈를 내 추적 목록에 추가합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        404: {"description": "이슈를 찾을 수 없음 (`E_RESOURCE_002`)", "model": ErrorResponse},
        409: {"description": "이미 추적 중인 이슈 (`E_CONFLICT_002`)", "model": ErrorResponse},
    },
)
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


@router.delete(
    "/{issue_id}/track",
    summary="이슈 추적 해제",
    description="추적 중인 이슈를 내 추적 목록에서 제거합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        404: {"description": "이슈를 찾을 수 없음 (`E_RESOURCE_002`)", "model": ErrorResponse},
    },
)
def untrack_issue(issue_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = IssueService(IssueRepository(db))
    if service.get_issue(issue_id) is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)
    service.untrack_issue(user_id=user_id, issue_id=issue_id)
    db.commit()
    return success_response(request=request, data=None, message="이슈 추적 해제 완료")


@router.post(
    "/{issue_id}/triggers",
    summary="트리거 생성 (관리자)",
    description="이슈에 새 트리거(사건 경과)를 등록합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    status_code=201,
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "이슈를 찾을 수 없음 (`E_RESOURCE_002`)", "model": ErrorResponse},
    },
)
def create_trigger(
    issue_id: str,
    payload: CreateTriggerRequest,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    service = IssueService(IssueRepository(db))
    created = service.create_trigger(
        issue_id=issue_id,
        occurred_at=payload.occurredAt,
        summary=payload.summary,
        trigger_type=payload.type.value,
        source_ids=payload.sourceIds,
    )
    if created is None:
        raise AppError(code="E_RESOURCE_002", message="이슈를 찾을 수 없습니다.", status_code=404)

    db.commit()
    return success_response(
        request=request, data=created, status_code=201, message="트리거 생성 성공"
    )
