"""피드 관련 스케줄러 잡.

- issue_rankings: 매시 정각 — 활성 이슈별 랭킹 스냅샷 계산
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.db.enums import IssueStatus, UpdateType
from src.models.events import user_saved_events
from src.models.feed import EventUpdate
from src.models.issues import Issue, IssueRankSnapshot

logger = logging.getLogger(__name__)

# 점수 가중치
W_RECENT_UPDATES = 0.4
W_SAVED_COUNT = 0.2
W_TRACKED_COUNT = 0.2
W_SOURCE_WEIGHT = 0.2

TOP_N = 20
RETENTION_DAYS = 7


def calculate_issue_rankings(db: Session) -> str | None:
    """활성 이슈별 최근 24시간 지표를 집계하여 상위 20개 랭킹 스냅샷을 저장한다."""
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)

    # 활성 이슈 목록
    active_issues = db.execute(
        select(Issue.id, Issue.tracker_count).where(
            Issue.status.in_([IssueStatus.ONGOING, IssueStatus.REIGNITED])
        )
    ).all()

    if not active_issues:
        logger.info("[issue_rankings] 활성 이슈 없음")
        return "active_issues=0"

    scored: list[tuple[str, float, int, int, int]] = []

    for issue_id, tracker_count in active_issues:
        # 최근 24시간 event_updates 수 (DUP 제외)
        recent_updates = db.execute(
            select(func.count(EventUpdate.id)).where(
                EventUpdate.issue_id == issue_id,
                EventUpdate.update_type != UpdateType.DUP,
                EventUpdate.created_at >= since_24h,
            )
        ).scalar_one()

        # 저장 수 (user_saved_events에서 이슈에 연결된 이벤트의 저장 수)
        saved_count = db.execute(
            select(func.count(user_saved_events.c.user_id)).where(
                user_saved_events.c.event_id.in_(
                    select(EventUpdate.article_id).where(EventUpdate.issue_id == issue_id)
                )
            )
        ).scalar_one()

        # 다양한 소스 수 (source diversity → source_weight)
        from src.models.pipeline import RawArticle

        source_count = db.execute(
            select(func.count(func.distinct(RawArticle.source_name)))
            .join(EventUpdate, EventUpdate.article_id == RawArticle.id)
            .where(
                EventUpdate.issue_id == issue_id,
                EventUpdate.created_at >= since_24h,
                EventUpdate.update_type != UpdateType.DUP,
            )
        ).scalar_one()

        # source_weight: 1~5개 소스는 0.2~1.0 비례
        source_weight = min(source_count / 5.0, 1.0)

        score = (
            W_RECENT_UPDATES * min(recent_updates / 10.0, 1.0)
            + W_SAVED_COUNT * min(saved_count / 50.0, 1.0)
            + W_TRACKED_COUNT * min(tracker_count / 100.0, 1.0)
            + W_SOURCE_WEIGHT * source_weight
        )

        scored.append((issue_id, score, recent_updates, tracker_count, saved_count))

    # 점수 기준 내림차순 정렬 → 상위 TOP_N
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:TOP_N]

    # 스냅샷 저장
    for rank_idx, (issue_id, score, recent_updates, tracked_count, saved_count) in enumerate(
        top, start=1
    ):
        db.add(
            IssueRankSnapshot(
                id=str(uuid4()),
                issue_id=issue_id,
                rank=rank_idx,
                score=round(score, 4),
                recent_updates=recent_updates,
                tracked_count=tracked_count,
                saved_count=saved_count,
                calculated_at=now,
                created_at=now,
            )
        )

    # 7일 이전 스냅샷 삭제
    cutoff = now - timedelta(days=RETENTION_DAYS)
    deleted = db.execute(
        delete(IssueRankSnapshot).where(IssueRankSnapshot.calculated_at < cutoff)
    ).rowcount

    db.flush()

    detail = f"issues={len(active_issues)}, top={len(top)}, deleted_old={deleted}"
    logger.info(f"[issue_rankings] {detail}")
    return detail
