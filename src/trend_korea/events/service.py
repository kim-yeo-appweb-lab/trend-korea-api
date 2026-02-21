from datetime import datetime, timezone

from trend_korea.core.exceptions import AppError
from trend_korea.core.pagination import decode_cursor, encode_cursor
from trend_korea.events.repository import EventRepository


class EventService:
    def __init__(self, repository: EventRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def list_events(
        self,
        *,
        size: int,
        cursor: str | None,
        sort: str,
        importance: str | None,
        verification_status: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_events(
            size=size,
            offset=offset,
            sort=sort,
            importance=importance,
            verification_status=verification_status,
            from_at=from_at,
            to_at=to_at,
        )
        return [self._to_item(event) for event in items], encode_cursor(next_offset) if next_offset is not None else None

    def get_event(self, event_id: str) -> dict | None:
        event = self.repository.get_event(event_id)
        if event is None:
            return None
        return self._to_item(event)

    def save_event(self, *, user_id: str, event_id: str) -> tuple[bool, str | None]:
        saved = self.repository.save_for_user(user_id=user_id, event_id=event_id)
        return saved, self._to_iso(datetime.now(timezone.utc))

    def unsave_event(self, *, user_id: str, event_id: str) -> bool:
        return self.repository.unsave_for_user(user_id=user_id, event_id=event_id)

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
    ) -> dict:
        if tag_ids:
            count = self.repository.count_tags_by_ids(tag_ids)
            if count != len(tag_ids):
                raise AppError(
                    code="E_VALID_002",
                    message="존재하지 않는 태그가 포함되어 있습니다.",
                    status_code=400,
                )
        if source_ids:
            count = self.repository.count_sources_by_ids(source_ids)
            if count != len(source_ids):
                raise AppError(
                    code="E_VALID_002",
                    message="존재하지 않는 출처가 포함되어 있습니다.",
                    status_code=400,
                )
        event = self.repository.create_event(
            occurred_at=occurred_at,
            title=title,
            summary=summary,
            importance=importance,
            verification_status=verification_status,
            tag_ids=tag_ids,
            source_ids=source_ids,
        )
        return self._to_item(event)

    def update_event(
        self,
        *,
        event_id: str,
        title: str | None,
        summary: str | None,
        importance: str | None,
        verification_status: str | None,
        tag_ids: list[str] | None,
        source_ids: list[str] | None,
    ) -> dict | None:
        event = self.repository.get_event(event_id)
        if event is None:
            return None
        updated = self.repository.update_event(
            event=event,
            title=title,
            summary=summary,
            importance=importance,
            verification_status=verification_status,
            tag_ids=tag_ids,
            source_ids=source_ids,
        )
        return self._to_item(updated)

    def delete_event(self, *, event_id: str) -> bool:
        event = self.repository.get_event(event_id)
        if event is None:
            return False
        self.repository.delete_event(event)
        return True

    def list_saved_events(
        self,
        *,
        user_id: str,
        size: int,
        cursor: str | None,
        sort: str,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_saved_events(
            user_id=user_id,
            size=size,
            offset=offset,
            sort=sort,
        )
        saved_at_by_event = self.repository.list_saved_at_by_event_ids_for_user(
            user_id=user_id,
            event_ids=[event.id for event in items],
        )

        payload = []
        for event in items:
            item = self._to_item(event)
            item["savedAt"] = self._to_iso(saved_at_by_event.get(event.id))
            payload.append(item)

        return payload, encode_cursor(next_offset) if next_offset is not None else None

    def _to_item(self, event) -> dict:
        sources = self.repository.list_sources(event.id)
        return {
            "id": event.id,
            "occurredAt": self._to_iso(event.occurred_at),
            "title": event.title,
            "summary": event.summary,
            "tags": [],
            "sources": [
                {
                    "url": source.url,
                    "title": source.title,
                    "publisher": source.publisher,
                    "publishedAt": self._to_iso(source.published_at),
                }
                for source in sources
            ],
            "importance": event.importance.value,
            "verificationStatus": event.verification_status.value,
            "relatedIssueIds": [],
            "sourceCount": len(sources),
            "createdAt": self._to_iso(event.created_at),
            "updatedAt": self._to_iso(event.updated_at),
        }
