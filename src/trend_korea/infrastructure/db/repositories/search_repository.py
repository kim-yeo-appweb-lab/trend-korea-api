from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from trend_korea.infrastructure.db.models.community import Post
from trend_korea.infrastructure.db.models.event import Event
from trend_korea.infrastructure.db.models.search import SearchRanking
from trend_korea.infrastructure.db.models.issue import Issue


class SearchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        *,
        q: str,
        entity_type: str,
        sort: str,
        size: int,
        offset: int,
    ) -> tuple[list[dict], int | None, int]:
        keyword = q.strip()
        if not keyword:
            return [], None, 0

        q_like = f"%{keyword}%"
        results: list[dict] = []

        if entity_type in {"all", "event"}:
            events = self.db.execute(
                select(Event)
                .where((Event.title.ilike(q_like)) | (Event.summary.ilike(q_like)))
                .limit(100)
            ).scalars().all()
            for event in events:
                score = 2 if event.title.lower().startswith(keyword.lower()) else 1
                results.append(
                    {
                        "entityType": "event",
                        "id": event.id,
                        "title": event.title,
                        "summary": event.summary,
                        "date": event.occurred_at.isoformat(),
                        "score": score,
                    }
                )

        if entity_type in {"all", "issue"}:
            issues = self.db.execute(
                select(Issue)
                .where((Issue.title.ilike(q_like)) | (Issue.description.ilike(q_like)))
                .limit(100)
            ).scalars().all()
            for issue in issues:
                score = 2 if issue.title.lower().startswith(keyword.lower()) else 1
                results.append(
                    {
                        "entityType": "issue",
                        "id": issue.id,
                        "title": issue.title,
                        "summary": issue.description,
                        "date": issue.updated_at.isoformat(),
                        "score": score,
                    }
                )

        if entity_type in {"all", "post"}:
            posts = self.db.execute(
                select(Post)
                .where((Post.title.ilike(q_like)) | (Post.content.ilike(q_like)))
                .limit(100)
            ).scalars().all()
            for post in posts:
                score = 2 if post.title.lower().startswith(keyword.lower()) else 1
                results.append(
                    {
                        "entityType": "post",
                        "id": post.id,
                        "title": post.title,
                        "summary": post.content[:120],
                        "date": post.created_at.isoformat(),
                        "score": score,
                    }
                )

        if sort == "-createdAt":
            results.sort(key=lambda item: item["date"], reverse=True)
        elif sort == "-popularity":
            results.sort(key=lambda item: item.get("score", 0), reverse=True)
        else:
            results.sort(key=lambda item: item.get("score", 0), reverse=True)

        total_count = len(results)
        paged = results[offset : offset + size + 1]
        has_next = len(paged) > size
        items = paged[:size]
        next_offset = offset + size if has_next else None

        for item in items:
            item.pop("score", None)

        return items, next_offset, total_count

    def suggestions(self, *, q: str, limit: int = 10) -> list[str]:
        keyword = q.strip()
        if not keyword:
            return []

        q_like = f"{keyword}%"
        values: list[str] = []

        for model, field in ((Event, Event.title), (Issue, Issue.title), (Post, Post.title)):
            rows = self.db.execute(select(field).where(field.ilike(q_like)).limit(limit)).scalars().all()
            for row in rows:
                if row not in values:
                    values.append(row)
                if len(values) >= limit:
                    return values
        return values

    def rankings(self, *, limit: int = 10) -> list[dict]:
        latest = self.db.execute(
            select(SearchRanking.calculated_at)
            .order_by(desc(SearchRanking.calculated_at))
            .limit(1)
        ).scalar_one_or_none()

        if latest is None:
            return []

        rows = self.db.execute(
            select(SearchRanking)
            .where(SearchRanking.calculated_at == latest)
            .order_by(SearchRanking.rank.asc())
            .limit(limit)
        ).scalars().all()

        return [
            {
                "keyword": row.keyword,
                "rank": row.rank,
                "score": row.score,
                "calculatedAt": row.calculated_at.isoformat(),
            }
            for row in rows
        ]
