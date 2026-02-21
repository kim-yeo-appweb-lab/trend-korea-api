from trend_korea.events.service import EventService
from trend_korea.issues.service import IssueService


class TrackingService:
    def __init__(self, issue_service: IssueService, event_service: EventService) -> None:
        self.issue_service = issue_service
        self.event_service = event_service

    def tracked_issues(
        self,
        *,
        user_id: str,
        size: int,
        cursor: str | None,
        sort: str,
    ) -> tuple[list[dict], str | None]:
        return self.issue_service.list_tracked_issues(
            user_id=user_id,
            size=size,
            cursor=cursor,
            sort=sort,
        )

    def saved_events(
        self,
        *,
        user_id: str,
        size: int,
        cursor: str | None,
        sort: str,
    ) -> tuple[list[dict], str | None]:
        return self.event_service.list_saved_events(
            user_id=user_id,
            size=size,
            cursor=cursor,
            sort=sort,
        )
