"""키워드 구독 데이터 액세스 계층."""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.pipeline import RawArticle
from src.models.subscription import KeywordMatch, KeywordSubscription


class SubscriptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_subscription(self, sub: KeywordSubscription) -> KeywordSubscription:
        self.db.add(sub)
        self.db.flush()
        return sub

    def list_subscriptions(self, *, user_id: str) -> list[KeywordSubscription]:
        stmt = (
            select(KeywordSubscription)
            .where(KeywordSubscription.user_id == user_id)
            .order_by(desc(KeywordSubscription.created_at))
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_subscription(self, *, subscription_id: str, user_id: str) -> KeywordSubscription | None:
        stmt = select(KeywordSubscription).where(
            KeywordSubscription.id == subscription_id,
            KeywordSubscription.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete_subscription(self, sub: KeywordSubscription) -> None:
        self.db.delete(sub)
        self.db.flush()

    def list_active_subscriptions_by_keywords(
        self, *, keywords: list[str]
    ) -> list[KeywordSubscription]:
        """키워드 목록에 매칭되는 활성 구독 조회 (파이프라인 연동용)."""
        if not keywords:
            return []
        stmt = select(KeywordSubscription).where(
            KeywordSubscription.keyword.in_(keywords),
            KeywordSubscription.is_active.is_(True),
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_matches(
        self,
        *,
        subscription_id: str,
        offset: int,
        limit: int,
    ) -> tuple[list[dict], int | None]:
        stmt = (
            select(KeywordMatch, RawArticle)
            .join(RawArticle, KeywordMatch.article_id == RawArticle.id)
            .where(KeywordMatch.subscription_id == subscription_id)
            .order_by(desc(KeywordMatch.matched_at))
        )
        rows = self.db.execute(stmt.offset(offset).limit(limit + 1)).all()
        has_next = len(rows) > limit
        items = rows[:limit]
        next_offset = offset + limit if has_next else None

        result = []
        for match, article in items:
            result.append({"match": match, "article": article})
        return result, next_offset

    def bulk_create_matches(self, matches: list[KeywordMatch]) -> None:
        self.db.add_all(matches)
        self.db.flush()
