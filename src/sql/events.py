from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import asc, delete, desc, func, insert, select, update
from sqlalchemy.orm import Session

from src.db.enums import Importance, VerificationStatus
from src.models.events import Event, event_tags, user_saved_events
from src.models.sources import Source
from src.models.tags import Tag


class EventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _apply_sort(self, stmt, sort: str):
        sort_map = {
            "occurredAt": Event.occurred_at,
            "importance": Event.importance,
            "createdAt": Event.created_at,
        }
        orders = []
        for token in [v.strip() for v in sort.split(",") if v.strip()]:
            desc_mode = token.startswith("-")
            key = token[1:] if desc_mode else token
            column = sort_map.get(key)
            if column is None:
                continue
            orders.append(desc(column) if desc_mode else asc(column))
        if not orders:
            orders = [desc(Event.occurred_at)]
        return stmt.order_by(*orders)

    def list_events(
        self,
        *,
        size: int,
        offset: int,
        sort: str,
        importance: str | None,
        verification_status: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
    ) -> tuple[list[Event], int | None]:
        stmt = select(Event)
        if importance:
            stmt = stmt.where(Event.importance == Importance(importance))
        if verification_status:
            stmt = stmt.where(Event.verification_status == VerificationStatus(verification_status))
        if from_at:
            stmt = stmt.where(Event.occurred_at >= from_at)
        if to_at:
            stmt = stmt.where(Event.occurred_at <= to_at)
        stmt = self._apply_sort(stmt, sort)
        rows = self.db.execute(stmt.offset(offset).limit(size + 1)).scalars().all()
        has_next = len(rows) > size
        items = rows[:size]
        next_offset = offset + size if has_next else None
        return items, next_offset

    def get_event(self, event_id: str) -> Event | None:
        stmt = select(Event).where(Event.id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_sources(self, event_id: str) -> list[Source]:
        stmt = (
            select(Source)
            .where(Source.entity_type == "event", Source.entity_id == event_id)
            .order_by(desc(Source.published_at))
        )
        return self.db.execute(stmt).scalars().all()

    def save_for_user(self, *, user_id: str, event_id: str) -> bool:
        exists_stmt = select(user_saved_events.c.user_id).where(
            user_saved_events.c.user_id == user_id,
            user_saved_events.c.event_id == event_id,
        )
        exists = self.db.execute(exists_stmt).first()
        if exists:
            return False
        self.db.execute(
            insert(user_saved_events).values(
                user_id=user_id,
                event_id=event_id,
                saved_at=datetime.now(timezone.utc),
            )
        )
        return True

    def unsave_for_user(self, *, user_id: str, event_id: str) -> bool:
        result = self.db.execute(
            delete(user_saved_events).where(
                user_saved_events.c.user_id == user_id,
                user_saved_events.c.event_id == event_id,
            )
        )
        return bool(result.rowcount)

    def create_event(
        self,
        *,
        occurred_at: datetime,
        title: str,
        summary: str,
        importance: str,
        verification_status: str,
        tag_ids: list[str],
        source_ids: list[str],
    ) -> Event:
        now = datetime.now(timezone.utc)
        event = Event(
            id=str(uuid4()),
            occurred_at=occurred_at,
            title=title,
            summary=summary,
            importance=Importance(importance),
            verification_status=VerificationStatus(verification_status),
            source_count=len(source_ids),
            created_at=now,
            updated_at=now,
        )
        self.db.add(event)
        self.db.flush()

        if tag_ids:
            self.db.execute(
                insert(event_tags),
                [{"event_id": event.id, "tag_id": tag_id} for tag_id in tag_ids],
            )

        if source_ids:
            self.db.execute(
                update(Source)
                .where(Source.id.in_(source_ids))
                .values(entity_type="event", entity_id=event.id)
            )

        self.db.flush()
        return event

    def update_event(
        self,
        *,
        event: Event,
        title: str | None,
        summary: str | None,
        importance: str | None,
        verification_status: str | None,
        tag_ids: list[str] | None,
        source_ids: list[str] | None,
    ) -> Event:
        if title is not None:
            event.title = title
        if summary is not None:
            event.summary = summary
        if importance is not None:
            event.importance = Importance(importance)
        if verification_status is not None:
            event.verification_status = VerificationStatus(verification_status)

        if tag_ids is not None:
            self.db.execute(delete(event_tags).where(event_tags.c.event_id == event.id))
            if tag_ids:
                self.db.execute(
                    insert(event_tags),
                    [{"event_id": event.id, "tag_id": tag_id} for tag_id in tag_ids],
                )

        if source_ids is not None:
            if source_ids:
                self.db.execute(
                    update(Source)
                    .where(Source.id.in_(source_ids))
                    .values(entity_type="event", entity_id=event.id)
                )
            event.source_count = len(source_ids)

        event.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return event

    def delete_event(self, event: Event) -> None:
        self.db.delete(event)
        self.db.flush()

    def list_saved_events(
        self,
        *,
        user_id: str,
        size: int,
        offset: int,
        sort: str,
    ) -> tuple[list[Event], int | None]:
        stmt = (
            select(Event)
            .join(
                user_saved_events,
                user_saved_events.c.event_id == Event.id,
            )
            .where(user_saved_events.c.user_id == user_id)
        )
        stmt = self._apply_sort(stmt, sort)
        rows = self.db.execute(stmt.offset(offset).limit(size + 1)).scalars().all()
        has_next = len(rows) > size
        items = rows[:size]
        next_offset = offset + size if has_next else None
        return items, next_offset

    def list_saved_at_by_event_ids_for_user(
        self, *, user_id: str, event_ids: list[str]
    ) -> dict[str, datetime]:
        if not event_ids:
            return {}
        rows = self.db.execute(
            select(user_saved_events.c.event_id, user_saved_events.c.saved_at).where(
                user_saved_events.c.user_id == user_id,
                user_saved_events.c.event_id.in_(event_ids),
            )
        ).all()
        return {row.event_id: row.saved_at for row in rows}

    def count_tags_by_ids(self, tag_ids: list[str]) -> int:
        if not tag_ids:
            return 0
        stmt = select(func.count(Tag.id)).where(Tag.id.in_(tag_ids))
        return int(self.db.execute(stmt).scalar_one())

    def count_sources_by_ids(self, source_ids: list[str]) -> int:
        if not source_ids:
            return 0
        stmt = select(func.count(Source.id)).where(Source.id.in_(source_ids))
        return int(self.db.execute(stmt).scalar_one())

    def count_saved_events(self, *, user_id: str) -> int:
        stmt = (
            select(func.count(Event.id))
            .select_from(Event)
            .join(user_saved_events, user_saved_events.c.event_id == Event.id)
            .where(user_saved_events.c.user_id == user_id)
        )
        return int(self.db.execute(stmt).scalar_one())
