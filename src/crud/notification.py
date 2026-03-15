"""알림 비즈니스 로직."""

from datetime import datetime, timezone
from uuid import uuid4

from src.core.pagination import decode_cursor, encode_cursor
from src.models.notification import Notification, UserAlertRule
from src.sql.notification import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    # ── Alert Rules ──

    def create_alert_rule(
        self,
        *,
        user_id: str,
        keyword: str | None,
        min_importance: float | None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        rule = self.repository.create_alert_rule(
            UserAlertRule(
                id=str(uuid4()),
                user_id=user_id,
                keyword=keyword,
                min_importance=min_importance,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        return self._rule_to_dict(rule)

    def list_alert_rules(self, *, user_id: str) -> list[dict]:
        rules = self.repository.list_alert_rules(user_id=user_id)
        return [self._rule_to_dict(r) for r in rules]

    def delete_alert_rule(self, *, rule_id: str, user_id: str) -> bool:
        rule = self.repository.get_alert_rule(rule_id=rule_id, user_id=user_id)
        if rule is None:
            return False
        self.repository.delete_alert_rule(rule)
        return True

    def _rule_to_dict(self, rule: UserAlertRule) -> dict:
        return {
            "id": rule.id,
            "keyword": rule.keyword,
            "minImportance": rule.min_importance,
            "isActive": rule.is_active,
            "createdAt": self._to_iso(rule.created_at),
        }

    # ── Notifications ──

    def list_notifications(
        self,
        *,
        user_id: str,
        cursor: str | None,
        size: int,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_notifications(
            user_id=user_id,
            offset=offset,
            limit=size,
        )

        payload = [self._notification_to_dict(n) for n in items]
        next_cursor = encode_cursor(next_offset) if next_offset is not None else None
        return payload, next_cursor

    def mark_read(self, *, notification_id: str, user_id: str) -> dict | None:
        notification = self.repository.get_notification(
            notification_id=notification_id,
            user_id=user_id,
        )
        if notification is None:
            return None
        self.repository.mark_read(notification)
        return self._notification_to_dict(notification)

    def mark_all_read(self, *, user_id: str) -> int:
        return self.repository.mark_all_read(user_id=user_id)

    def _notification_to_dict(self, n: Notification) -> dict:
        return {
            "id": n.id,
            "type": n.type.value,
            "title": n.title,
            "message": n.message,
            "entityType": n.entity_type,
            "entityId": n.entity_id,
            "isRead": n.is_read,
            "createdAt": self._to_iso(n.created_at),
        }
