from fastapi import APIRouter, Request

from src.utils.dependencies import CurrentAdminUserId, DbSession
from src.schemas.shared import ErrorResponse, RESPONSE_400, RESPONSE_401, RESPONSE_403_ADMIN
from src.schemas.triggers import UpdateTriggerRequest
from src.core.exceptions import AppError
from src.core.response import success_response
from src.sql.issues import IssueRepository
from src.sql.triggers import TriggerRepository

router = APIRouter(prefix="/triggers", tags=["triggers"])


@router.patch(
    "/{trigger_id}",
    summary="트리거 수정 (관리자)",
    description="트리거(사건 경과) 정보를 수정합니다. 변경할 필드만 전송합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "트리거를 찾을 수 없음 (`E_RESOURCE_005`)", "model": ErrorResponse},
    },
)
def update_trigger(
    trigger_id: str,
    payload: UpdateTriggerRequest,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    repo = TriggerRepository(db)
    trigger = repo.get_trigger(trigger_id)
    if trigger is None:
        raise AppError(code="E_RESOURCE_005", message="트리거를 찾을 수 없습니다.", status_code=404)

    updated = repo.update_trigger(
        trigger=trigger,
        summary=payload.summary,
        trigger_type=payload.type.value if payload.type is not None else None,
        occurred_at=payload.occurredAt,
    )
    db.commit()

    return success_response(
        request=request,
        data={
            "id": updated.id,
            "summary": updated.summary,
            "updatedAt": updated.updated_at.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
        },
        message="트리거 수정 성공",
    )


@router.delete(
    "/{trigger_id}",
    summary="트리거 삭제 (관리자)",
    description="트리거를 삭제합니다. 삭제 후 이슈의 최신 트리거 일시가 자동 갱신됩니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "트리거를 찾을 수 없음 (`E_RESOURCE_005`)", "model": ErrorResponse},
    },
)
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
