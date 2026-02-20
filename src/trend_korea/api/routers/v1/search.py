from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import DbSession
from trend_korea.application.search.service import SearchService
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.search_repository import SearchRepository

router = APIRouter(prefix="/search", tags=["search"])

def _build_search_response(*, items: list[dict], page: int, limit: int) -> dict:
    mapped_items = [
        {
            "id": item["id"],
            "type": item["entityType"],
            "title": item["title"],
            "summary": item["summary"],
            "date": item["date"],
            "tags": [],
        }
        for item in items
    ]
    return {
        "items": mapped_items,
        "pagination": {
            "currentPage": page,
            "totalPages": 0,
            "totalItems": 0,
            "itemsPerPage": limit,
            "hasNext": False,
            "hasPrev": page > 1,
        },
    }


@router.get("")
def search(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    tab: str = Query(default="all", pattern="^(all|events|issues|community)$"),
    sortBy: str = Query(default="relevance"),
):
    service = SearchService(SearchRepository(db))
    entity_type_map = {
        "all": "all",
        "events": "event",
        "issues": "issue",
        "community": "post",
    }
    entity_type = entity_type_map.get(tab, "all")
    sort = f"-{sortBy}"

    from trend_korea.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None

    items, _, total_items = service.search(
        q=q,
        entity_type=entity_type,
        sort=sort,
        size=limit,
        cursor=cursor,
    )

    response_data = _build_search_response(items=items, page=page, limit=limit)
    total_pages = (total_items + limit - 1) // limit if total_items else 0
    response_data["pagination"] = {
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
        "itemsPerPage": limit,
        "hasNext": page < total_pages,
        "hasPrev": page > 1,
    }
    return success_response(
        request=request,
        data=response_data,
        message="검색 성공",
    )


@router.get("/events")
def search_events(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sortBy: str = Query(default="relevance"),
):
    service = SearchService(SearchRepository(db))
    from trend_korea.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None
    items, _, total_items = service.search(q=q, entity_type="event", sort=f"-{sortBy}", size=limit, cursor=cursor)
    response_data = _build_search_response(items=items, page=page, limit=limit)
    total_pages = (total_items + limit - 1) // limit if total_items else 0
    response_data["pagination"] = {
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
        "itemsPerPage": limit,
        "hasNext": page < total_pages,
        "hasPrev": page > 1,
    }
    return success_response(
        request=request,
        data=response_data,
        message="검색 성공",
    )


@router.get("/issues")
def search_issues(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sortBy: str = Query(default="relevance"),
):
    service = SearchService(SearchRepository(db))
    from trend_korea.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None
    items, _, total_items = service.search(q=q, entity_type="issue", sort=f"-{sortBy}", size=limit, cursor=cursor)
    response_data = _build_search_response(items=items, page=page, limit=limit)
    total_pages = (total_items + limit - 1) // limit if total_items else 0
    response_data["pagination"] = {
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
        "itemsPerPage": limit,
        "hasNext": page < total_pages,
        "hasPrev": page > 1,
    }
    return success_response(
        request=request,
        data=response_data,
        message="검색 성공",
    )


@router.get("/posts")
def search_posts(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sortBy: str = Query(default="relevance"),
):
    service = SearchService(SearchRepository(db))
    from trend_korea.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None
    items, _, total_items = service.search(q=q, entity_type="post", sort=f"-{sortBy}", size=limit, cursor=cursor)
    response_data = _build_search_response(items=items, page=page, limit=limit)
    total_pages = (total_items + limit - 1) // limit if total_items else 0
    response_data["pagination"] = {
        "currentPage": page,
        "totalPages": total_pages,
        "totalItems": total_items,
        "itemsPerPage": limit,
        "hasNext": page < total_pages,
        "hasPrev": page > 1,
    }
    return success_response(
        request=request,
        data=response_data,
        message="검색 성공",
    )
