from fastapi import APIRouter, Query, Request

from src.utils.dependencies import DbSession
from src.core.response import success_response
from src.sql.home import HomeRepository

router = APIRouter(prefix="/home", tags=["home"])


@router.get(
    "/breaking-news",
    summary="속보 목록",
    description="최신 속보 사건 목록을 조회합니다. 발생 시간, 제목, 요약, 중요도를 포함합니다.",
)
def breaking_news(
    request: Request,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=20, description="조회할 속보 수 (1~20)"),
):
    repo = HomeRepository(db)
    items = repo.list_breaking_news(limit=limit)
    return success_response(
        request=request,
        data=[
            {
                "id": item.id,
                "number": idx + 1,
                "time": item.occurred_at.strftime("%H:%M"),
                "title": item.title,
                "summary": item.summary,
                "tags": [],
                "importance": item.importance.value,
            }
            for idx, item in enumerate(items)
        ],
        message="조회 성공",
    )


@router.get(
    "/hot-posts",
    summary="인기 게시글 목록",
    description="특정 기간 내 인기 게시글 목록을 조회합니다. 댓글 수 기준으로 정렬됩니다.",
)
def hot_posts(
    request: Request,
    db: DbSession,
    limit: int = Query(default=5, ge=1, le=20, description="조회할 게시글 수 (1~20)"),
    period: str = Query(default="24h", description="집계 기간 (예: 24h, 7d)"),
):
    _ = period
    repo = HomeRepository(db)
    items = repo.list_hot_posts(limit=limit)
    return success_response(
        request=request,
        data=[
            {
                "id": item.id,
                "number": idx + 1,
                "title": item.title,
                "category": None,
                "commentCount": item.comment_count,
                "author": None,
                "createdAt": item.created_at.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                ),
                "isHot": True,
            }
            for idx, item in enumerate(items)
        ],
        message="조회 성공",
    )


@router.get(
    "/search-rankings",
    summary="검색어 랭킹",
    description="인기 검색어 랭킹을 조회합니다. 일간/주간 기준으로 집계됩니다.",
)
def search_rankings(
    request: Request,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=20, description="상위 랭킹 수 (1~20)"),
    period: str = Query(
        default="daily",
        pattern="^(daily|weekly)$",
        description="집계 기간 (daily: 일간, weekly: 주간)",
    ),
):
    _ = period
    repo = HomeRepository(db)
    items = repo.list_search_rankings(limit=limit)
    return success_response(
        request=request,
        data=[
            {
                "rank": item.rank,
                "keyword": item.keyword,
                "count": item.score,
                "change": "-",
            }
            for item in items
        ],
        message="조회 성공",
    )


@router.get(
    "/trending",
    summary="트렌딩 이슈",
    description="현재 주목받는 이슈 목록을 조회합니다. 관련 사건 수, 추적자 수 등의 지표를 포함합니다.",
)
def trending(
    request: Request,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=20, description="조회할 이슈 수 (1~20)"),
    period: str = Query(default="24h", description="집계 기간 (예: 24h, 7d)"),
):
    _ = period
    repo = HomeRepository(db)
    items = repo.list_trending_events(limit=limit)
    return success_response(
        request=request,
        data=[
            {
                "rank": idx + 1,
                "issue": {
                    "id": item.id,
                    "title": item.title,
                    "status": "ongoing",
                },
                "relatedEventCount": 0,
                "trackerCount": 0,
                "change": "-",
            }
            for idx, item in enumerate(items)
        ],
        message="조회 성공",
    )


@router.get(
    "/timeline-minimap",
    summary="타임라인 미니맵",
    description="최근 N일간의 사건 발생 밀도를 날짜별로 조회합니다. 타임라인 시각화에 사용됩니다.",
)
def timeline_minimap(
    request: Request,
    db: DbSession,
    days: int = Query(default=7, ge=1, le=30, description="조회할 일수 (1~30)"),
):
    repo = HomeRepository(db)
    items = repo.list_timeline_events(limit=days)
    return success_response(
        request=request,
        data={
            "dates": [
                {
                    "date": item.occurred_at.date().isoformat(),
                    "eventCount": 1,
                    "density": "high" if item.importance.value == "high" else "low",
                }
                for item in items
            ]
        },
        message="조회 성공",
    )


@router.get(
    "/featured-news",
    summary="주요 뉴스",
    description="편집자가 선별한 주요 뉴스 게시글 목록을 조회합니다.",
)
def featured_news(
    request: Request,
    db: DbSession,
    limit: int = Query(default=5, ge=1, le=20, description="조회할 뉴스 수 (1~20)"),
):
    repo = HomeRepository(db)
    items = repo.list_featured_news(limit=limit)
    return success_response(
        request=request,
        data=[
            {
                "id": item.id,
                "author": None,
                "authorImage": None,
                "title": item.title,
                "summary": item.summary,
                "imageUrl": None,
                "createdAt": item.created_at.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                ),
            }
            for item in items
        ],
        message="조회 성공",
    )


@router.get(
    "/community-media",
    summary="커뮤니티 미디어 게시글",
    description="미디어(이미지 포함) 게시글 목록을 조회합니다.",
)
def community_media(
    request: Request,
    db: DbSession,
    limit: int = Query(default=6, ge=1, le=20, description="조회할 게시글 수 (1~20)"),
):
    repo = HomeRepository(db)
    items = repo.list_community_media_posts(limit=limit)
    return success_response(
        request=request,
        data=[
            {
                "id": item.id,
                "title": item.title,
                "imageUrl": None,
                "viewCount": 0,
                "createdAt": item.created_at.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                ),
            }
            for item in items
        ],
        message="조회 성공",
    )
