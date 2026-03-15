"""Feed 데이터 액세스 계층."""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from src.db.enums import FeedType, UpdateType
from src.models.feed import EventUpdate, LiveFeedItem
from src.models.issues import Issue, IssueRankSnapshot
from src.models.pipeline import RawArticle


class FeedRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_feed_items(
        self,
        *,
        feed_type: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[dict], int | None]:
        """피드 항목 목록 조회. JOIN으로 관련 데이터를 한번에 가져온다."""
        stmt = (
            select(
                LiveFeedItem,
                EventUpdate,
                RawArticle,
                Issue.id.label("issue_id_ref"),
                Issue.title.label("issue_title"),
            )
            .join(EventUpdate, LiveFeedItem.update_id == EventUpdate.id)
            .join(RawArticle, EventUpdate.article_id == RawArticle.id)
            .outerjoin(Issue, LiveFeedItem.issue_id == Issue.id)
        )

        if feed_type and feed_type != "all":
            stmt = stmt.where(LiveFeedItem.feed_type == FeedType(feed_type))

        stmt = stmt.order_by(
            desc(LiveFeedItem.rank_score),
            desc(LiveFeedItem.created_at),
        )

        rows = self.db.execute(stmt.offset(offset).limit(limit + 1)).all()
        has_next = len(rows) > limit
        items = rows[:limit]
        next_offset = offset + limit if has_next else None

        result = []
        for lfi, eu, ra, issue_id_ref, issue_title in items:
            result.append(
                {
                    "lfi": lfi,
                    "eu": eu,
                    "ra": ra,
                    "issue_id": issue_id_ref,
                    "issue_title": issue_title,
                }
            )

        return result, next_offset

    def count_feed_items(self, *, feed_type: str | None) -> int:
        """피드 항목 전체 개수."""
        stmt = select(func.count(LiveFeedItem.id))
        if feed_type and feed_type != "all":
            stmt = stmt.where(LiveFeedItem.feed_type == FeedType(feed_type))
        return int(self.db.execute(stmt).scalar_one())

    def list_top_stories(self, *, limit: int) -> tuple[list[dict], str | None]:
        """최신 랭킹 스냅샷에서 Top Stories를 조회한다."""
        # 가장 최근 calculated_at 시각 조회
        latest_at = self.db.execute(
            select(func.max(IssueRankSnapshot.calculated_at))
        ).scalar_one_or_none()

        if latest_at is None:
            return [], None

        stmt = (
            select(IssueRankSnapshot, Issue.title.label("issue_title"))
            .join(Issue, IssueRankSnapshot.issue_id == Issue.id)
            .where(IssueRankSnapshot.calculated_at == latest_at)
            .order_by(IssueRankSnapshot.rank)
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()

        # 각 이슈의 마지막 업데이트 시각 조회
        result = []
        for snapshot, issue_title in rows:
            last_update = self.db.execute(
                select(func.max(EventUpdate.created_at)).where(
                    EventUpdate.issue_id == snapshot.issue_id,
                    EventUpdate.update_type != UpdateType.DUP,
                )
            ).scalar_one_or_none()

            result.append(
                {
                    "snapshot": snapshot,
                    "issue_title": issue_title,
                    "last_update_at": last_update,
                }
            )

        calculated_at_iso = latest_at.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        return result, calculated_at_iso

    def list_issue_updates(
        self,
        *,
        issue_id: str,
        offset: int,
        limit: int,
    ) -> tuple[list[dict], int | None]:
        """이슈 타임라인 조회. EventUpdate + RawArticle JOIN."""
        stmt = (
            select(EventUpdate, RawArticle)
            .join(RawArticle, EventUpdate.article_id == RawArticle.id)
            .where(
                EventUpdate.issue_id == issue_id,
                EventUpdate.update_type != UpdateType.DUP,
            )
            .order_by(desc(EventUpdate.created_at))
        )

        rows = self.db.execute(stmt.offset(offset).limit(limit + 1)).all()
        has_next = len(rows) > limit
        items = rows[:limit]
        next_offset = offset + limit if has_next else None

        result = []
        for eu, ra in items:
            result.append({"eu": eu, "ra": ra})

        return result, next_offset
