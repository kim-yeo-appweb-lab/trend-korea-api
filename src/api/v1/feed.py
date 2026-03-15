"""Feed 라우터 — 실시간 뉴스 업데이트 피드."""

from fastapi import APIRouter, Query, Request

from src.core.response import success_response
from src.crud.feed import FeedService
from src.sql.feed import FeedRepository
from src.utils.dependencies import DbSession

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get(
    "/top",
    summary="Top Stories 조회",
    description="현재 가장 주목받는 이슈 랭킹을 조회합니다. 매시 정각 계산됩니다.",
)
def list_top_stories(
    request: Request,
    db: DbSession,
    limit: int = Query(
        default=10,
        ge=1,
        le=20,
        description="조회할 항목 수",
    ),
):
    service = FeedService(FeedRepository(db))
    items, calculated_at = service.list_top_stories(limit=limit)
    return success_response(
        request=request,
        data={
            "items": items,
            "calculatedAt": calculated_at,
        },
        message="조회 성공",
    )


@router.get(
    "/live",
    summary="실시간 피드 조회",
    description=(
        "실시간 뉴스 업데이트 피드를 조회합니다. "
        "`type` 파라미터로 속보(breaking), 주요(major), 전체(all) 필터링이 가능합니다."
    ),
)
def list_live_feed(
    request: Request,
    db: DbSession,
    type: str | None = Query(
        default=None,
        pattern="^(breaking|major|all)$",
        description="피드 유형 필터 (breaking, major, all). 미지정 시 전체 조회.",
    ),
    cursor: str | None = Query(
        default=None,
        description="다음 페이지 커서 토큰",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="한 번에 조회할 항목 수",
    ),
):
    service = FeedService(FeedRepository(db))
    items, next_cursor = service.list_live_feed(
        feed_type=type,
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
