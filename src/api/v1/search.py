from fastapi import APIRouter, Query, Request

from src.utils.dependencies import DbSession
from src.schemas.shared import RESPONSE_400
from src.crud.search import SearchService
from src.core.response import success_response
from src.sql.search import SearchRepository

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


@router.get(
    "",
    summary="통합 검색",
    description="사건, 이슈, 게시글을 통합 검색합니다. `tab` 파라미터로 검색 범위를 지정할 수 있습니다. 페이지 기반 페이지네이션을 사용합니다.",
    responses={**RESPONSE_400},
)
def search(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1, description="검색어 (최소 1자)"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 결과 수"),
    tab: str = Query(
        default="all",
        pattern="^(all|events|issues|community)$",
        description="검색 범위 (all, events, issues, community)",
    ),
    sortBy: str = Query(
        default="relevance", description="정렬 기준 (relevance: 관련도, createdAt: 작성일)"
    ),
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

    from src.core.pagination import encode_cursor

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


@router.get(
    "/events",
    summary="사건 검색",
    description="사건만을 대상으로 검색합니다. 페이지 기반 페이지네이션을 사용합니다.",
    responses={**RESPONSE_400},
)
def search_events(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1, description="검색어 (최소 1자)"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 결과 수"),
    sortBy: str = Query(default="relevance", description="정렬 기준 (relevance, createdAt)"),
):
    service = SearchService(SearchRepository(db))
    from src.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None
    items, _, total_items = service.search(
        q=q, entity_type="event", sort=f"-{sortBy}", size=limit, cursor=cursor
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


@router.get(
    "/issues",
    summary="이슈 검색",
    description="이슈만을 대상으로 검색합니다. 페이지 기반 페이지네이션을 사용합니다.",
    responses={**RESPONSE_400},
)
def search_issues(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1, description="검색어 (최소 1자)"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 결과 수"),
    sortBy: str = Query(default="relevance", description="정렬 기준 (relevance, createdAt)"),
):
    service = SearchService(SearchRepository(db))
    from src.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None
    items, _, total_items = service.search(
        q=q, entity_type="issue", sort=f"-{sortBy}", size=limit, cursor=cursor
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


@router.get(
    "/posts",
    summary="게시글 검색",
    description="게시글만을 대상으로 검색합니다. 페이지 기반 페이지네이션을 사용합니다.",
    responses={**RESPONSE_400},
)
def search_posts(
    request: Request,
    db: DbSession,
    q: str = Query(min_length=1, description="검색어 (최소 1자)"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 결과 수"),
    sortBy: str = Query(default="relevance", description="정렬 기준 (relevance, createdAt)"),
):
    service = SearchService(SearchRepository(db))
    from src.core.pagination import encode_cursor

    offset = (page - 1) * limit
    cursor = encode_cursor(offset) if offset > 0 else None
    items, _, total_items = service.search(
        q=q, entity_type="post", sort=f"-{sortBy}", size=limit, cursor=cursor
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
