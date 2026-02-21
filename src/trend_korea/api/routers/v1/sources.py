from datetime import datetime

from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentAdminUserId, DbSession
from trend_korea.api.schemas.common import ErrorResponse, RESPONSE_400, RESPONSE_401, RESPONSE_403_ADMIN
from trend_korea.api.schemas.sources import CreateSourceRequest
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.source_repository import SourceRepository

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get(
    "",
    summary="출처 목록 조회",
    description="등록된 출처(뉴스 기사 등) 목록을 페이지 기반 페이지네이션으로 조회합니다. 발행 매체명으로 필터링할 수 있습니다.",
)
def list_sources(
    request: Request,
    db: DbSession,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="한 페이지에 조회할 항목 수"),
    publisher: str | None = Query(default=None, description="발행 매체명 필터"),
):
    repo = SourceRepository(db)
    items, total = repo.list_sources(page=page, limit=limit, publisher=publisher)
    total_pages = (total + limit - 1) // limit if total else 0
    return success_response(
        request=request,
        data={
            "items": [
                {
                    "id": source.id,
                    "title": source.title,
                    "url": source.url,
                    "publisher": source.publisher,
                    "publishedAt": source.published_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    "reliabilityScore": None,
                }
                for source in items
            ],
            "pagination": {
                "currentPage": page,
                "totalPages": total_pages,
                "totalItems": total,
                "itemsPerPage": limit,
                "hasNext": page < total_pages,
                "hasPrev": page > 1,
            },
        },
        message="조회 성공",
    )


@router.post(
    "",
    summary="출처 등록 (관리자)",
    description="새 출처(뉴스 기사 등)를 등록합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    status_code=201,
    responses={**RESPONSE_400, **RESPONSE_401, **RESPONSE_403_ADMIN},
)
def create_source(payload: CreateSourceRequest, request: Request, db: DbSession, _: CurrentAdminUserId):
    repo = SourceRepository(db)
    created = repo.create_source(
        url=payload.url,
        title=payload.title,
        publisher=payload.publisher,
        published_at=payload.publishedAt,
    )
    db.commit()
    return success_response(
        request=request,
        data={
            "id": created.id,
            "title": created.title,
            "url": created.url,
            "publisher": created.publisher,
            "publishedAt": created.published_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "createdAt": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        },
        status_code=201,
        message="출처 등록 성공",
    )


@router.delete(
    "/{source_id}",
    summary="출처 삭제 (관리자)",
    description="출처를 삭제합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "출처를 찾을 수 없음 (`E_RESOURCE_007`)", "model": ErrorResponse},
    },
)
def delete_source(source_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    repo = SourceRepository(db)
    source = repo.get_source(source_id)
    if source is None:
        raise AppError(code="E_RESOURCE_007", message="출처를 찾을 수 없습니다.", status_code=404)

    repo.delete_source(source)
    db.commit()
    return success_response(request=request, data=None, message="출처 삭제 성공")
