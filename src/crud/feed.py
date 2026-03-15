"""Feed 비즈니스 로직."""

from datetime import datetime

from src.core.pagination import decode_cursor, encode_cursor
from src.sql.feed import FeedRepository


class FeedService:
    def __init__(self, repository: FeedRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def list_live_feed(
        self,
        *,
        feed_type: str | None,
        cursor: str | None,
        size: int,
    ) -> tuple[list[dict], str | None]:
        """실시간 피드 목록 조회."""
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_feed_items(
            feed_type=feed_type,
            offset=offset,
            limit=size,
        )

        payload = []
        for row in items:
            lfi = row["lfi"]
            eu = row["eu"]
            ra = row["ra"]
            payload.append(
                {
                    "id": lfi.id,
                    "issueId": row["issue_id"],
                    "issueTitle": row["issue_title"],
                    "updateType": eu.update_type.value,
                    "updateScore": eu.update_score,
                    "feedType": lfi.feed_type.value,
                    "rankScore": lfi.rank_score,
                    "article": {
                        "title": ra.title,
                        "source": ra.source_name,
                        "publishedAt": self._to_iso(ra.published_at),
                        "url": ra.original_url,
                    },
                    "majorReasons": eu.major_reasons or [],
                    "diffSummary": eu.diff_summary,
                    "createdAt": self._to_iso(lfi.created_at),
                }
            )

        next_cursor = encode_cursor(next_offset) if next_offset is not None else None
        return payload, next_cursor

    def list_top_stories(self, *, limit: int) -> tuple[list[dict], str | None]:
        """Top Stories 조회."""
        rows, calculated_at = self.repository.list_top_stories(limit=limit)

        payload = []
        for row in rows:
            snapshot = row["snapshot"]
            payload.append(
                {
                    "rank": snapshot.rank,
                    "issueId": snapshot.issue_id,
                    "issueTitle": row["issue_title"],
                    "score": snapshot.score,
                    "recentUpdates": snapshot.recent_updates,
                    "trackedCount": snapshot.tracked_count,
                    "lastUpdateAt": self._to_iso(row["last_update_at"]),
                }
            )

        return payload, calculated_at

    def list_issue_timeline(
        self,
        *,
        issue_id: str,
        cursor: str | None,
        size: int,
    ) -> tuple[list[dict], str | None]:
        """이슈 타임라인 조회."""
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_issue_updates(
            issue_id=issue_id,
            offset=offset,
            limit=size,
        )

        payload = []
        for row in items:
            eu = row["eu"]
            ra = row["ra"]
            payload.append(
                {
                    "updateType": eu.update_type.value,
                    "summary": ra.title,
                    "diffSummary": eu.diff_summary,
                    "sources": [
                        {
                            "title": ra.title,
                            "url": ra.original_url,
                            "source": ra.source_name,
                            "publishedAt": self._to_iso(ra.published_at),
                        }
                    ],
                    "occurredAt": self._to_iso(eu.created_at),
                }
            )

        next_cursor = encode_cursor(next_offset) if next_offset is not None else None
        return payload, next_cursor
