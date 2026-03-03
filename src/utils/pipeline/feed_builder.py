"""피드 빌더 모듈.

분류 결과를 DB에 저장하고, 피드 항목을 생성한다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.enums import FeedType, UpdateType
from src.db.event_update import EventUpdate
from src.db.issue_keyword_state import IssueKeywordState
from src.db.live_feed_item import LiveFeedItem
from src.utils.pipeline.update_classifier import ClassificationResult


def _determine_feed_entries(
    result: ClassificationResult,
) -> list[tuple[FeedType, float]]:
    """분류 결과에 따라 생성할 피드 항목의 (타입, rank_score) 목록을 반환."""
    settings = get_settings()

    if result.update_type == UpdateType.DUP:
        return []

    score = result.update_score

    if result.update_type == UpdateType.NEW:
        return [(FeedType.ALL, score)]

    if result.update_type == UpdateType.MINOR_UPDATE:
        return [(FeedType.ALL, score)]

    if result.update_type == UpdateType.MAJOR_UPDATE:
        boosted = score * settings.feed_major_boost
        entries = [
            (FeedType.ALL, boosted),
            (FeedType.MAJOR, boosted),
        ]
        if score >= settings.feed_breaking_score_threshold:
            entries.append((FeedType.BREAKING, score * 2.0))
        return entries

    return []


def build_feed_items(
    results: list[ClassificationResult],
    event_update_map: dict[str, str],
) -> list[LiveFeedItem]:
    """분류 결과로부터 LiveFeedItem 목록을 생성한다."""
    now = datetime.now(timezone.utc)
    items: list[LiveFeedItem] = []

    for result in results:
        update_id = event_update_map.get(result.article_id)
        if not update_id:
            continue

        entries = _determine_feed_entries(result)
        for feed_type, rank_score in entries:
            items.append(
                LiveFeedItem(
                    id=str(uuid4()),
                    issue_id=result.matched_issue_id,
                    update_id=update_id,
                    feed_type=feed_type,
                    rank_score=rank_score,
                    created_at=now,
                )
            )

    return items


def _update_keyword_states(
    result: ClassificationResult, db: Session
) -> None:
    """매칭된 이슈의 키워드 상태를 갱신한다."""
    if not result.matched_issue_id:
        return

    now = datetime.now(timezone.utc)
    stmt = (
        select(IssueKeywordState)
        .where(IssueKeywordState.issue_id == result.matched_issue_id)
    )
    states = db.execute(stmt).scalars().all()
    for state in states:
        state.last_seen_at = now
    db.flush()


def persist_results(
    results: list[ClassificationResult], db: Session
) -> dict[str, int]:
    """분류 결과를 DB에 저장하고 통계를 반환한다.

    Returns:
        {"new": N, "minor": N, "major": N, "dup": N}
    """
    now = datetime.now(timezone.utc)
    stats = {"new": 0, "minor": 0, "major": 0, "dup": 0}
    event_update_map: dict[str, str] = {}  # article_id -> event_update.id

    for result in results:
        # 통계 집계
        if result.update_type == UpdateType.NEW:
            stats["new"] += 1
        elif result.update_type == UpdateType.MINOR_UPDATE:
            stats["minor"] += 1
        elif result.update_type == UpdateType.MAJOR_UPDATE:
            stats["major"] += 1
        elif result.update_type == UpdateType.DUP:
            stats["dup"] += 1
            continue  # DUP은 EventUpdate/Feed 생성 안 함

        # EventUpdate 중복 검사 (article_id + issue_id)
        existing = db.execute(
            select(EventUpdate.id).where(
                EventUpdate.article_id == result.article_id,
                EventUpdate.issue_id == result.matched_issue_id
                if result.matched_issue_id
                else EventUpdate.issue_id.is_(None),
            )
        ).scalar_one_or_none()

        if existing:
            event_update_map[result.article_id] = existing
            continue

        eu_id = str(uuid4())
        eu = EventUpdate(
            id=eu_id,
            issue_id=result.matched_issue_id,
            article_id=result.article_id,
            update_type=result.update_type,
            update_score=result.update_score,
            major_reasons=result.major_reasons if result.major_reasons else None,
            diff_summary=result.diff_summary or None,
            duplicate_of_id=result.duplicate_of_id,
            created_at=now,
        )
        db.add(eu)
        event_update_map[result.article_id] = eu_id

        # 키워드 상태 갱신
        _update_keyword_states(result, db)

    db.flush()

    # LiveFeedItem 생성
    non_dup_results = [r for r in results if r.update_type != UpdateType.DUP]
    feed_items = build_feed_items(non_dup_results, event_update_map)
    for item in feed_items:
        db.add(item)

    db.flush()
    return stats
