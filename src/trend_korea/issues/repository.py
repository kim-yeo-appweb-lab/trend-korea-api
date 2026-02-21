from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import asc, delete, desc, func, insert, select, update
from sqlalchemy.orm import Session

from trend_korea.db.enums import IssueStatus, SourceEntityType
from trend_korea.db.enums import TriggerType
from trend_korea.issues.models import Issue, issue_events, issue_tags, user_tracked_issues
from trend_korea.sources.models import Source
from trend_korea.triggers.models import Trigger


class IssueRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _apply_sort(self, stmt, sort: str):
        sort_map = {
            "latestTriggerAt": Issue.latest_trigger_at,
            "trackerCount": Issue.tracker_count,
            "createdAt": Issue.created_at,
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
            orders = [desc(Issue.latest_trigger_at), desc(Issue.created_at)]
        return stmt.order_by(*orders)

    def list_issues(
        self,
        *,
        size: int,
        offset: int,
        sort: str,
        status: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
    ) -> tuple[list[Issue], int | None]:
        stmt = select(Issue)
        if status:
            stmt = stmt.where(Issue.status == IssueStatus(status))
        if from_at:
            stmt = stmt.where(Issue.updated_at >= from_at)
        if to_at:
            stmt = stmt.where(Issue.updated_at <= to_at)
        stmt = self._apply_sort(stmt, sort)
        rows = self.db.execute(stmt.offset(offset).limit(size + 1)).scalars().all()
        has_next = len(rows) > size
        items = rows[:size]
        next_offset = offset + size if has_next else None
        return items, next_offset

    def count_issues(
        self,
        *,
        status: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
    ) -> int:
        stmt = select(func.count(Issue.id))
        if status:
            stmt = stmt.where(Issue.status == IssueStatus(status))
        if from_at:
            stmt = stmt.where(Issue.updated_at >= from_at)
        if to_at:
            stmt = stmt.where(Issue.updated_at <= to_at)
        return int(self.db.execute(stmt).scalar_one())

    def get_issue(self, issue_id: str) -> Issue | None:
        stmt = select(Issue).where(Issue.id == issue_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_sources(self, issue_id: str) -> list[Source]:
        stmt = (
            select(Source)
            .where(Source.entity_type == "issue", Source.entity_id == issue_id)
            .order_by(desc(Source.published_at))
        )
        return self.db.execute(stmt).scalars().all()

    def list_triggers(
        self,
        *,
        issue_id: str,
        size: int,
        offset: int,
    ) -> tuple[list[Trigger], int | None]:
        stmt = (
            select(Trigger)
            .where(Trigger.issue_id == issue_id)
            .order_by(desc(Trigger.occurred_at))
        )
        rows = self.db.execute(stmt.offset(offset).limit(size + 1)).scalars().all()
        has_next = len(rows) > size
        items = rows[:size]
        next_offset = offset + size if has_next else None
        return items, next_offset

    def list_trigger_sources(self, trigger_id: str) -> list[Source]:
        stmt = (
            select(Source)
            .where(Source.entity_type == SourceEntityType.TRIGGER, Source.entity_id == trigger_id)
            .order_by(desc(Source.published_at))
        )
        return self.db.execute(stmt).scalars().all()

    def track_for_user(self, *, user_id: str, issue_id: str) -> bool:
        exists_stmt = select(user_tracked_issues.c.user_id).where(
            user_tracked_issues.c.user_id == user_id,
            user_tracked_issues.c.issue_id == issue_id,
        )
        exists = self.db.execute(exists_stmt).first()
        if exists:
            return False
        self.db.execute(
            insert(user_tracked_issues).values(
                user_id=user_id,
                issue_id=issue_id,
                tracked_at=datetime.now(timezone.utc),
            )
        )
        issue = self.get_issue(issue_id)
        if issue:
            issue.tracker_count += 1
            self.db.flush()
        return True

    def untrack_for_user(self, *, user_id: str, issue_id: str) -> bool:
        result = self.db.execute(
            delete(user_tracked_issues).where(
                user_tracked_issues.c.user_id == user_id,
                user_tracked_issues.c.issue_id == issue_id,
            )
        )
        removed = bool(result.rowcount)
        if removed:
            issue = self.get_issue(issue_id)
            if issue and issue.tracker_count > 0:
                issue.tracker_count -= 1
                self.db.flush()
        return removed

    def create_issue(
        self,
        *,
        title: str,
        description: str,
        status: str,
        tag_ids: list[str],
        source_ids: list[str],
        related_event_ids: list[str],
    ) -> Issue:
        now = datetime.now(timezone.utc)
        issue = Issue(
            id=str(uuid4()),
            title=title,
            description=description,
            status=IssueStatus(status),
            tracker_count=0,
            latest_trigger_at=None,
            created_at=now,
            updated_at=now,
        )
        self.db.add(issue)
        self.db.flush()

        if tag_ids:
            self.db.execute(
                insert(issue_tags),
                [{"issue_id": issue.id, "tag_id": tag_id} for tag_id in tag_ids],
            )

        if related_event_ids:
            self.db.execute(
                insert(issue_events),
                [{"issue_id": issue.id, "event_id": event_id} for event_id in related_event_ids],
            )

        if source_ids:
            self.db.execute(
                update(Source)
                .where(Source.id.in_(source_ids))
                .values(entity_type="issue", entity_id=issue.id)
            )

        self.db.flush()
        return issue

    def update_issue(
        self,
        *,
        issue: Issue,
        title: str | None,
        description: str | None,
        status: str | None,
        tag_ids: list[str] | None,
        source_ids: list[str] | None,
        related_event_ids: list[str] | None,
    ) -> Issue:
        if title is not None:
            issue.title = title
        if description is not None:
            issue.description = description
        if status is not None:
            issue.status = IssueStatus(status)

        if tag_ids is not None:
            self.db.execute(delete(issue_tags).where(issue_tags.c.issue_id == issue.id))
            if tag_ids:
                self.db.execute(
                    insert(issue_tags),
                    [{"issue_id": issue.id, "tag_id": tag_id} for tag_id in tag_ids],
                )

        if related_event_ids is not None:
            self.db.execute(delete(issue_events).where(issue_events.c.issue_id == issue.id))
            if related_event_ids:
                self.db.execute(
                    insert(issue_events),
                    [{"issue_id": issue.id, "event_id": event_id} for event_id in related_event_ids],
                )

        if source_ids is not None:
            if source_ids:
                self.db.execute(
                    update(Source)
                    .where(Source.id.in_(source_ids))
                    .values(entity_type="issue", entity_id=issue.id)
                )

        issue.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return issue

    def delete_issue(self, issue: Issue) -> None:
        self.db.delete(issue)
        self.db.flush()

    def list_latest_triggers_by_issue_ids(self, issue_ids: list[str]) -> dict[str, Trigger]:
        if not issue_ids:
            return {}

        items = (
            self.db.execute(
                select(Trigger)
                .where(Trigger.issue_id.in_(issue_ids))
                .order_by(Trigger.issue_id.asc(), Trigger.occurred_at.desc())
            )
            .scalars()
            .all()
        )

        latest: dict[str, Trigger] = {}
        for trigger in items:
            if trigger.issue_id not in latest:
                latest[trigger.issue_id] = trigger
        return latest

    def list_tracked_at_by_issue_ids_for_user(self, *, user_id: str, issue_ids: list[str]) -> dict[str, datetime]:
        if not issue_ids:
            return {}
        rows = self.db.execute(
            select(user_tracked_issues.c.issue_id, user_tracked_issues.c.tracked_at).where(
                user_tracked_issues.c.user_id == user_id,
                user_tracked_issues.c.issue_id.in_(issue_ids),
            )
        ).all()
        return {row.issue_id: row.tracked_at for row in rows}

    def attach_sources_to_trigger(self, *, trigger_id: str, source_ids: list[str]) -> None:
        if not source_ids:
            return
        self.db.execute(
            update(Source)
            .where(Source.id.in_(source_ids))
            .values(entity_type=SourceEntityType.TRIGGER, entity_id=trigger_id)
        )
        self.db.flush()

    def create_trigger(
        self,
        *,
        issue_id: str,
        occurred_at: datetime,
        summary: str,
        trigger_type: str,
    ) -> Trigger:
        now = datetime.now(timezone.utc)
        trigger = Trigger(
            id=str(uuid4()),
            issue_id=issue_id,
            occurred_at=occurred_at,
            summary=summary,
            type=TriggerType(trigger_type),
            created_at=now,
            updated_at=now,
        )
        self.db.add(trigger)

        issue = self.get_issue(issue_id)
        if issue is not None:
            issue.latest_trigger_at = occurred_at
            issue.updated_at = now

        self.db.flush()
        return trigger

    def list_tracked_issues(
        self,
        *,
        user_id: str,
        size: int,
        offset: int,
        sort: str,
    ) -> tuple[list[Issue], int | None]:
        stmt = select(Issue).join(
            user_tracked_issues,
            user_tracked_issues.c.issue_id == Issue.id,
        ).where(user_tracked_issues.c.user_id == user_id)
        stmt = self._apply_sort(stmt, sort)
        rows = self.db.execute(stmt.offset(offset).limit(size + 1)).scalars().all()
        has_next = len(rows) > size
        items = rows[:size]
        next_offset = offset + size if has_next else None
        return items, next_offset

    def count_tracked_issues(self, *, user_id: str) -> int:
        stmt = (
            select(func.count(Issue.id))
            .select_from(Issue)
            .join(user_tracked_issues, user_tracked_issues.c.issue_id == Issue.id)
            .where(user_tracked_issues.c.user_id == user_id)
        )
        return int(self.db.execute(stmt).scalar_one())
