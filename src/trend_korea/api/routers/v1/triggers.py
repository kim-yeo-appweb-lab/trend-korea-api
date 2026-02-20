from datetime import datetime

from fastapi import APIRouter, Request

from trend_korea.api.deps import CurrentAdminUserId, DbSession
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.domain.enums import TriggerType
from trend_korea.infrastructure.db.repositories.issue_repository import IssueRepository
from trend_korea.infrastructure.db.repositories.trigger_repository import TriggerRepository

router = APIRouter(prefix="/triggers", tags=["triggers"])


@router.patch("/{trigger_id}")
def update_trigger(
    trigger_id: str,
    payload: dict,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    repo = TriggerRepository(db)
    trigger = repo.get_trigger(trigger_id)
    if trigger is None:
        raise AppError(code="E_RESOURCE_005", message="트리거를 찾을 수 없습니다.", status_code=404)

    trigger_type = payload.get("type")
    occurred_at = payload.get("occurredAt")
    parsed_occurred_at = None
    if occurred_at is not None:
        try:
            parsed_occurred_at = datetime.fromisoformat(str(occurred_at).replace("Z", "+00:00"))
        except ValueError as exc:
            raise AppError(code="E_VALID_002", message="occurredAt 형식이 올바르지 않습니다.", status_code=400) from exc

    if trigger_type is not None:
        try:
            TriggerType(trigger_type)
        except ValueError as exc:
            raise AppError(code="E_VALID_002", message="type 값이 올바르지 않습니다.", status_code=400) from exc

    updated = repo.update_trigger(
        trigger=trigger,
        summary=payload.get("summary"),
        trigger_type=trigger_type,
        occurred_at=parsed_occurred_at,
    )
    db.commit()

    return success_response(
        request=request,
        data={
            "id": updated.id,
            "summary": updated.summary,
            "updatedAt": updated.updated_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        },
        message="트리거 수정 성공",
    )


@router.delete("/{trigger_id}")
def delete_trigger(trigger_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    repo = TriggerRepository(db)
    trigger = repo.get_trigger(trigger_id)
    if trigger is None:
        raise AppError(code="E_RESOURCE_005", message="트리거를 찾을 수 없습니다.", status_code=404)

    issue_repo = IssueRepository(db)
    issue = issue_repo.get_issue(trigger.issue_id)

    repo.delete_trigger(trigger)

    if issue is not None:
        items, _ = issue_repo.list_triggers(issue_id=issue.id, size=1, offset=0)
        issue.latest_trigger_at = items[0].occurred_at if items else None

    db.commit()
    return success_response(request=request, data=None, message="트리거 삭제 성공")
