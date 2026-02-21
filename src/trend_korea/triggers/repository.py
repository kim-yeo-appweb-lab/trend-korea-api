from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from trend_korea.db.enums import TriggerType
from trend_korea.triggers.models import Trigger


class TriggerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_trigger(self, trigger_id: str) -> Trigger | None:
        stmt = select(Trigger).where(Trigger.id == trigger_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_trigger(
        self,
        *,
        trigger: Trigger,
        summary: str | None,
        trigger_type: str | None,
        occurred_at: datetime | None,
    ) -> Trigger:
        if summary is not None:
            trigger.summary = summary
        if trigger_type is not None:
            trigger.type = TriggerType(trigger_type)
        if occurred_at is not None:
            trigger.occurred_at = occurred_at
        trigger.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return trigger

    def delete_trigger(self, trigger: Trigger) -> None:
        self.db.delete(trigger)
        self.db.flush()
