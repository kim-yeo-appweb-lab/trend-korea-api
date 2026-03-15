"""알림 데이터 액세스 계층."""

from sqlalchemy import desc, select, update
from sqlalchemy.orm import Session

from src.models.notification import Notification, UserAlertRule


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Alert Rules ──

    def create_alert_rule(self, rule: UserAlertRule) -> UserAlertRule:
        self.db.add(rule)
        self.db.flush()
        return rule

    def list_alert_rules(self, *, user_id: str) -> list[UserAlertRule]:
        stmt = (
            select(UserAlertRule)
            .where(UserAlertRule.user_id == user_id)
            .order_by(desc(UserAlertRule.created_at))
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_alert_rule(self, *, rule_id: str, user_id: str) -> UserAlertRule | None:
        stmt = select(UserAlertRule).where(
            UserAlertRule.id == rule_id,
            UserAlertRule.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete_alert_rule(self, rule: UserAlertRule) -> None:
        self.db.delete(rule)
        self.db.flush()

    def list_active_rules_by_keyword(self, *, keyword: str) -> list[UserAlertRule]:
        """특정 키워드에 매칭되는 활성 규칙 조회 (파이프라인 연동용)."""
        stmt = select(UserAlertRule).where(
            UserAlertRule.is_active.is_(True),
            (UserAlertRule.keyword == keyword) | (UserAlertRule.keyword.is_(None)),
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_active_rules_for_issue_trackers(self, *, user_ids: list[str]) -> list[UserAlertRule]:
        """특정 사용자들의 활성 규칙 조회 (이슈 추적자용)."""
        if not user_ids:
            return []
        stmt = select(UserAlertRule).where(
            UserAlertRule.user_id.in_(user_ids),
            UserAlertRule.is_active.is_(True),
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Notifications ──

    def create_notification(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification

    def bulk_create_notifications(self, notifications: list[Notification]) -> None:
        self.db.add_all(notifications)
        self.db.flush()

    def list_notifications(
        self,
        *,
        user_id: str,
        offset: int,
        limit: int,
    ) -> tuple[list[Notification], int | None]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
        )
        rows = self.db.execute(stmt.offset(offset).limit(limit + 1)).scalars().all()
        rows = list(rows)
        has_next = len(rows) > limit
        items = rows[:limit]
        next_offset = offset + limit if has_next else None
        return items, next_offset

    def get_notification(self, *, notification_id: str, user_id: str) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        self.db.flush()
        return notification

    def mark_all_read(self, *, user_id: str) -> int:
        result = self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        self.db.flush()
        return result.rowcount
