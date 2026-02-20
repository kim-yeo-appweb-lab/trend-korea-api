from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from trend_korea.infrastructure.db.models.community import Post
from trend_korea.infrastructure.db.models.event import Event
from trend_korea.infrastructure.db.models.search import SearchRanking


class HomeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_breaking_news(self, *, limit: int = 5) -> list[Event]:
        stmt = select(Event).order_by(desc(Event.occurred_at)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_hot_posts(self, *, limit: int = 5) -> list[Post]:
        stmt = select(Post).order_by(desc(Post.like_count), desc(Post.comment_count)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_search_rankings(self, *, limit: int = 10) -> list[SearchRanking]:
        stmt = select(SearchRanking).order_by(desc(SearchRanking.score)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_trending_events(self, *, limit: int = 10) -> list[Event]:
        stmt = select(Event).order_by(desc(Event.importance), desc(Event.occurred_at)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_timeline_events(self, *, limit: int = 10) -> list[Event]:
        stmt = select(Event).order_by(desc(Event.occurred_at)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_featured_news(self, *, limit: int = 6) -> list[Event]:
        stmt = select(Event).order_by(desc(Event.importance), desc(Event.created_at)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_community_media_posts(self, *, limit: int = 6) -> list[Post]:
        stmt = select(Post).order_by(desc(Post.created_at)).limit(limit)
        return self.db.execute(stmt).scalars().all()
