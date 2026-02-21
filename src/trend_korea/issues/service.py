from datetime import datetime

from trend_korea.core.pagination import decode_cursor, encode_cursor
from trend_korea.issues.repository import IssueRepository


class IssueService:
    def __init__(self, repository: IssueRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def list_issues(
        self,
        *,
        size: int,
        cursor: str | None,
        sort: str,
        status: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_issues(
            size=size,
            offset=offset,
            sort=sort,
            status=status,
            from_at=from_at,
            to_at=to_at,
        )
        return [self._to_item(issue) for issue in items], encode_cursor(next_offset) if next_offset is not None else None

    def get_issue(self, issue_id: str) -> dict | None:
        issue = self.repository.get_issue(issue_id)
        if issue is None:
            return None
        return self._to_item(issue)

    def create_issue(
        self,
        *,
        title: str,
        description: str,
        status: str,
        tag_ids: list[str],
        source_ids: list[str],
        related_event_ids: list[str],
    ) -> dict:
        issue = self.repository.create_issue(
            title=title,
            description=description,
            status=status,
            tag_ids=tag_ids,
            source_ids=source_ids,
            related_event_ids=related_event_ids,
        )
        return self._to_item(issue)

    def update_issue(
        self,
        *,
        issue_id: str,
        title: str | None,
        description: str | None,
        status: str | None,
        tag_ids: list[str] | None,
        source_ids: list[str] | None,
        related_event_ids: list[str] | None,
    ) -> dict | None:
        issue = self.repository.get_issue(issue_id)
        if issue is None:
            return None

        updated = self.repository.update_issue(
            issue=issue,
            title=title,
            description=description,
            status=status,
            tag_ids=tag_ids,
            source_ids=source_ids,
            related_event_ids=related_event_ids,
        )
        return self._to_item(updated)

    def delete_issue(self, *, issue_id: str) -> bool:
        issue = self.repository.get_issue(issue_id)
        if issue is None:
            return False
        self.repository.delete_issue(issue)
        return True

    def list_triggers(
        self,
        *,
        issue_id: str,
        size: int,
        cursor: str | None,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_triggers(issue_id=issue_id, size=size, offset=offset)
        payload = []
        for trigger in items:
            sources = self.repository.list_trigger_sources(trigger.id)
            payload.append(
                {
                    "id": trigger.id,
                    "issueId": trigger.issue_id,
                    "occurredAt": self._to_iso(trigger.occurred_at),
                    "summary": trigger.summary,
                    "type": trigger.type.value,
                    "sources": [
                        {
                            "url": source.url,
                            "title": source.title,
                            "publisher": source.publisher,
                            "publishedAt": self._to_iso(source.published_at),
                        }
                        for source in sources
                    ],
                    "createdAt": self._to_iso(trigger.created_at),
                    "updatedAt": self._to_iso(trigger.updated_at),
                }
            )
        return payload, encode_cursor(next_offset) if next_offset is not None else None

    def track_issue(self, *, user_id: str, issue_id: str) -> tuple[bool, str | None]:
        tracked = self.repository.track_for_user(user_id=user_id, issue_id=issue_id)
        return tracked, self._to_iso(datetime.utcnow())

    def untrack_issue(self, *, user_id: str, issue_id: str) -> bool:
        return self.repository.untrack_for_user(user_id=user_id, issue_id=issue_id)

    def create_trigger(
        self,
        *,
        issue_id: str,
        occurred_at: datetime,
        summary: str,
        trigger_type: str,
        source_ids: list[str],
    ) -> dict | None:
        issue = self.repository.get_issue(issue_id)
        if issue is None:
            return None
        trigger = self.repository.create_trigger(
            issue_id=issue_id,
            occurred_at=occurred_at,
            summary=summary,
            trigger_type=trigger_type,
        )
        self.repository.attach_sources_to_trigger(trigger_id=trigger.id, source_ids=source_ids)
        sources = self.repository.list_trigger_sources(trigger.id)
        return {
            "id": trigger.id,
            "issueId": trigger.issue_id,
            "occurredAt": self._to_iso(trigger.occurred_at),
            "summary": trigger.summary,
            "type": trigger.type.value,
            "sources": [
                {
                    "url": source.url,
                    "title": source.title,
                    "publisher": source.publisher,
                    "publishedAt": self._to_iso(source.published_at),
                }
                for source in sources
            ],
        }

    def list_tracked_issues(
        self,
        *,
        user_id: str,
        size: int,
        cursor: str | None,
        sort: str,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_tracked_issues(
            user_id=user_id,
            size=size,
            offset=offset,
            sort=sort,
        )
        latest_by_issue = self.repository.list_latest_triggers_by_issue_ids([issue.id for issue in items])
        tracked_at_by_issue = self.repository.list_tracked_at_by_issue_ids_for_user(
            user_id=user_id,
            issue_ids=[issue.id for issue in items],
        )

        payload = []
        for issue in items:
            latest = latest_by_issue.get(issue.id)
            tracked_at = tracked_at_by_issue.get(issue.id)
            payload.append(
                {
                    "id": issue.id,
                    "title": issue.title,
                    "status": issue.status.value,
                    "trackerCount": issue.tracker_count,
                    "latestTrigger": {
                        "summary": latest.summary if latest else None,
                        "occurredAt": self._to_iso(latest.occurred_at) if latest else None,
                    },
                    "trackedAt": self._to_iso(tracked_at),
                    "isNew": False,
                }
            )

        return payload, encode_cursor(next_offset) if next_offset is not None else None

    def _to_item(self, issue) -> dict:
        sources = self.repository.list_sources(issue.id)
        return {
            "id": issue.id,
            "title": issue.title,
            "description": issue.description,
            "status": issue.status.value,
            "tags": [],
            "triggers": [],
            "trackerCount": issue.tracker_count,
            "relatedEventIds": [],
            "sources": [
                {
                    "url": source.url,
                    "title": source.title,
                    "publisher": source.publisher,
                    "publishedAt": self._to_iso(source.published_at),
                }
                for source in sources
            ],
            "latestTriggerAt": self._to_iso(issue.latest_trigger_at),
            "createdAt": self._to_iso(issue.created_at),
            "updatedAt": self._to_iso(issue.updated_at),
        }
