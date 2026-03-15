"""키워드 구독 비즈니스 로직."""

from datetime import datetime, timezone
from uuid import uuid4

from src.core.pagination import decode_cursor, encode_cursor
from src.models.subscription import KeywordSubscription
from src.sql.subscription import SubscriptionRepository


class SubscriptionService:
    def __init__(self, repository: SubscriptionRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def create_subscription(self, *, user_id: str, keyword: str) -> dict:
        now = datetime.now(timezone.utc)
        sub = self.repository.create_subscription(
            KeywordSubscription(
                id=str(uuid4()),
                user_id=user_id,
                keyword=keyword.strip().lower(),
                is_active=True,
                created_at=now,
            )
        )
        return self._sub_to_dict(sub)

    def list_subscriptions(self, *, user_id: str) -> list[dict]:
        subs = self.repository.list_subscriptions(user_id=user_id)
        return [self._sub_to_dict(s) for s in subs]

    def delete_subscription(self, *, subscription_id: str, user_id: str) -> bool:
        sub = self.repository.get_subscription(
            subscription_id=subscription_id,
            user_id=user_id,
        )
        if sub is None:
            return False
        self.repository.delete_subscription(sub)
        return True

    def list_matches(
        self,
        *,
        subscription_id: str,
        user_id: str,
        cursor: str | None,
        size: int,
    ) -> tuple[list[dict], str | None] | None:
        # 구독 소유권 확인
        sub = self.repository.get_subscription(
            subscription_id=subscription_id,
            user_id=user_id,
        )
        if sub is None:
            return None

        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_matches(
            subscription_id=subscription_id,
            offset=offset,
            limit=size,
        )

        payload = []
        for row in items:
            match = row["match"]
            article = row["article"]
            payload.append(
                {
                    "id": match.id,
                    "articleId": article.id,
                    "articleTitle": article.title,
                    "articleUrl": article.original_url,
                    "source": article.source_name,
                    "matchedAt": self._to_iso(match.matched_at),
                }
            )

        next_cursor = encode_cursor(next_offset) if next_offset is not None else None
        return payload, next_cursor

    def _sub_to_dict(self, sub: KeywordSubscription) -> dict:
        return {
            "id": sub.id,
            "keyword": sub.keyword,
            "isActive": sub.is_active,
            "createdAt": self._to_iso(sub.created_at),
        }
