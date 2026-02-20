import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from trend_korea.infrastructure.db.models.community import Post
from trend_korea.infrastructure.db.models.event import Event
from trend_korea.infrastructure.db.models.issue import Issue
from trend_korea.infrastructure.db.models.search import SearchRanking

TOKEN_PATTERN = re.compile(r"[0-9A-Za-z가-힣]{2,}")


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def recalculate_search_rankings(db: Session) -> str:
    now = datetime.now(timezone.utc)
    from_at = now - timedelta(hours=24)

    counter: Counter[str] = Counter()

    events = db.execute(select(Event).where(Event.occurred_at >= from_at)).scalars().all()
    for event in events:
        counter.update(_tokens(event.title))

    issues = db.execute(select(Issue).where(Issue.updated_at >= from_at)).scalars().all()
    for issue in issues:
        counter.update(_tokens(issue.title))

    posts = db.execute(select(Post).where(Post.created_at >= from_at)).scalars().all()
    for post in posts:
        counter.update(_tokens(post.title))

    top_10 = counter.most_common(10)

    db.execute(delete(SearchRanking).where(SearchRanking.calculated_at < now - timedelta(days=7)))

    for index, (keyword, score) in enumerate(top_10, start=1):
        db.add(
            SearchRanking(
                id=str(uuid4()),
                keyword=keyword,
                rank=index,
                score=score,
                calculated_at=now,
            )
        )

    return f"ranked_keywords={len(top_10)}"
