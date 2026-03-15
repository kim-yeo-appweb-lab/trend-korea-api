"""피드 빌더 모듈.

분류 결과를 DB에 저장하고, 피드 항목을 생성한다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.enums import FeedType, NotificationType, UpdateType
from src.models.feed import EventUpdate, LiveFeedItem
from src.models.issues import IssueKeywordState, user_tracked_issues
from src.models.notification import Notification, UserAlertRule
from src.models.subscription import KeywordMatch, KeywordSubscription
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


def _update_keyword_states(result: ClassificationResult, db: Session) -> None:
    """매칭된 이슈의 키워드 상태를 갱신한다."""
    if not result.matched_issue_id:
        return

    now = datetime.now(timezone.utc)
    stmt = select(IssueKeywordState).where(IssueKeywordState.issue_id == result.matched_issue_id)
    states = db.execute(stmt).scalars().all()
    for state in states:
        state.last_seen_at = now
    db.flush()


def persist_results(results: list[ClassificationResult], db: Session) -> dict[str, int]:
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

    # MAJOR_UPDATE 알림 생성: 이슈 추적자의 활성 alert_rules 조회
    _create_major_update_notifications(results, db)

    # 키워드 구독 매칭: 새 기사의 키워드와 활성 구독 매칭
    _match_keyword_subscriptions(results, db)

    db.flush()
    return stats


def _create_major_update_notifications(results: list[ClassificationResult], db: Session) -> None:
    """MAJOR_UPDATE 분류 결과에 대해 이슈 추적자에게 알림을 생성한다."""
    now = datetime.now(timezone.utc)

    major_results = [
        r for r in results if r.update_type == UpdateType.MAJOR_UPDATE and r.matched_issue_id
    ]
    if not major_results:
        return

    # 이슈별 추적자 조회
    issue_ids = {r.matched_issue_id for r in major_results}
    tracker_rows = db.execute(
        select(
            user_tracked_issues.c.issue_id,
            user_tracked_issues.c.user_id,
        ).where(user_tracked_issues.c.issue_id.in_(issue_ids))
    ).all()

    if not tracker_rows:
        return

    # 이슈별 추적자 맵 구성
    issue_trackers: dict[str, list[str]] = {}
    for issue_id, user_id in tracker_rows:
        issue_trackers.setdefault(issue_id, []).append(user_id)

    # 추적자들의 활성 규칙 조회
    all_tracker_ids = list({uid for uids in issue_trackers.values() for uid in uids})
    active_rules = (
        db.execute(
            select(UserAlertRule).where(
                UserAlertRule.user_id.in_(all_tracker_ids),
                UserAlertRule.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )

    # 사용자별 규칙 맵
    user_rules: dict[str, list[UserAlertRule]] = {}
    for rule in active_rules:
        user_rules.setdefault(rule.user_id, []).append(rule)

    notifications: list[Notification] = []
    for result in major_results:
        tracker_user_ids = issue_trackers.get(result.matched_issue_id, [])
        for user_id in tracker_user_ids:
            rules = user_rules.get(user_id, [])
            # 규칙이 없으면 기본 알림 생성, 규칙이 있으면 조건 매칭
            should_notify = not rules  # 규칙 없으면 기본 알림
            for rule in rules:
                if rule.min_importance and result.update_score < rule.min_importance:
                    continue
                should_notify = True
                break

            if should_notify:
                title = "추적 중인 이슈에 주요 업데이트"
                message = f"점수: {result.update_score:.2f}" + (
                    f" | {result.diff_summary}" if result.diff_summary else ""
                )
                notifications.append(
                    Notification(
                        id=str(uuid4()),
                        user_id=user_id,
                        type=NotificationType.MAJOR_UPDATE,
                        title=title,
                        message=message,
                        entity_type="issue",
                        entity_id=result.matched_issue_id,
                        is_read=False,
                        created_at=now,
                    )
                )

    if notifications:
        db.add_all(notifications)


def _match_keyword_subscriptions(results: list[ClassificationResult], db: Session) -> None:
    """새 기사의 normalized_keywords와 활성 구독 키워드를 매칭한다."""
    now = datetime.now(timezone.utc)

    # DUP 제외, 키워드가 있는 결과만 필터
    non_dup_results = [r for r in results if r.update_type != UpdateType.DUP]
    if not non_dup_results:
        return

    # 모든 기사의 키워드 수집
    from src.models.pipeline import RawArticle

    article_ids = [r.article_id for r in non_dup_results]
    articles = db.execute(
        select(RawArticle.id, RawArticle.normalized_keywords).where(RawArticle.id.in_(article_ids))
    ).all()

    all_keywords: set[str] = set()
    article_keywords_map: dict[str, list[str]] = {}
    for article_id, keywords in articles:
        kws = keywords or []
        article_keywords_map[article_id] = kws
        all_keywords.update(kws)

    if not all_keywords:
        return

    # 활성 구독 조회
    active_subs = (
        db.execute(
            select(KeywordSubscription).where(
                KeywordSubscription.keyword.in_(all_keywords),
                KeywordSubscription.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )

    if not active_subs:
        return

    # 키워드별 구독 맵
    keyword_subs: dict[str, list[KeywordSubscription]] = {}
    for sub in active_subs:
        keyword_subs.setdefault(sub.keyword, []).append(sub)

    matches: list[KeywordMatch] = []
    notifications: list[Notification] = []

    for article_id, keywords in article_keywords_map.items():
        for kw in keywords:
            subs = keyword_subs.get(kw, [])
            for sub in subs:
                matches.append(
                    KeywordMatch(
                        id=str(uuid4()),
                        subscription_id=sub.id,
                        article_id=article_id,
                        matched_at=now,
                        created_at=now,
                    )
                )
                notifications.append(
                    Notification(
                        id=str(uuid4()),
                        user_id=sub.user_id,
                        type=NotificationType.KEYWORD_MATCH,
                        title=f"구독 키워드 '{kw}' 새 기사",
                        message=f"구독 키워드 '{kw}'와 매칭되는 새 기사가 수집되었습니다.",
                        entity_type="article",
                        entity_id=article_id,
                        is_read=False,
                        created_at=now,
                    )
                )

    if matches:
        db.add_all(matches)
    if notifications:
        db.add_all(notifications)
