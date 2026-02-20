from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import DbSession
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.home_repository import HomeRepository

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/breaking-news")
def breaking_news(request: Request, db: DbSession, limit: int = Query(default=10, ge=1, le=20)):
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


@router.get("/hot-posts")
def hot_posts(
    request: Request,
    db: DbSession,
    limit: int = Query(default=5, ge=1, le=20),
    period: str = Query(default="24h"),
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
                "createdAt": item.created_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "isHot": True,
            }
            for idx, item in enumerate(items)
        ],
        message="조회 성공",
    )


@router.get("/search-rankings")
def search_rankings(
    request: Request,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=20),
    period: str = Query(default="daily", pattern="^(daily|weekly)$"),
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


@router.get("/trending")
def trending(
    request: Request,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=20),
    period: str = Query(default="24h"),
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


@router.get("/timeline-minimap")
def timeline_minimap(request: Request, db: DbSession, days: int = Query(default=7, ge=1, le=30)):
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


@router.get("/featured-news")
def featured_news(request: Request, db: DbSession, limit: int = Query(default=5, ge=1, le=20)):
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
                "createdAt": item.created_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            }
            for item in items
        ],
        message="조회 성공",
    )


@router.get("/community-media")
def community_media(request: Request, db: DbSession, limit: int = Query(default=6, ge=1, le=20)):
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
                "createdAt": item.created_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            }
            for item in items
        ],
        message="조회 성공",
    )
