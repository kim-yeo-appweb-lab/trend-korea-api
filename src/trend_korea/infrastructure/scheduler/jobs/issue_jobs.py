from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from trend_korea.domain.enums import IssueStatus
from trend_korea.infrastructure.db.models.issue import Issue


def reconcile_issue_status(db: Session) -> str:
    now = datetime.now(timezone.utc)
    close_boundary = now - timedelta(days=30)
    reignite_boundary = now - timedelta(days=7)

    updated = 0
    rows = db.execute(select(Issue)).scalars().all()

    for issue in rows:
        latest = issue.latest_trigger_at
        if latest is None:
            continue

        target_status = issue.status
        if issue.status == IssueStatus.ONGOING and latest < close_boundary:
            target_status = IssueStatus.CLOSED
        elif issue.status == IssueStatus.CLOSED and latest >= reignite_boundary:
            target_status = IssueStatus.REIGNITED

        if target_status != issue.status:
            issue.status = target_status
            issue.updated_at = now
            updated += 1

    return f"updated={updated}"
