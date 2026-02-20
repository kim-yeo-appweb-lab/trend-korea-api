from datetime import datetime

from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentAdminUserId, DbSession
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.source_repository import SourceRepository

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
def list_sources(
    request: Request,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    publisher: str | None = Query(default=None),
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


@router.post("")
def create_source(payload: dict, request: Request, db: DbSession, _: CurrentAdminUserId):
    url = payload.get("url")
    title = payload.get("title")
    publisher = payload.get("publisher")
    published_at_raw = payload.get("publishedAt")
    if not url or not title or not publisher or not published_at_raw:
        raise AppError(code="E_VALID_001", message="필수 필드가 누락되었습니다.", status_code=400)

    try:
        published_at = datetime.fromisoformat(str(published_at_raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise AppError(code="E_VALID_002", message="publishedAt 형식이 올바르지 않습니다.", status_code=400) from exc

    repo = SourceRepository(db)
    created = repo.create_source(url=url, title=title, publisher=publisher, published_at=published_at)
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


@router.delete("/{source_id}")
def delete_source(source_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    repo = SourceRepository(db)
    source = repo.get_source(source_id)
    if source is None:
        raise AppError(code="E_RESOURCE_007", message="출처를 찾을 수 없습니다.", status_code=404)

    repo.delete_source(source)
    db.commit()
    return success_response(request=request, data=None, message="출처 삭제 성공")
