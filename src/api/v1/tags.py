from datetime import datetime, timezone

from fastapi import APIRouter, Query, Request

from src.utils.dependencies import CurrentAdminUserId, DbSession
from src.schemas.shared import ErrorResponse, RESPONSE_400, RESPONSE_401, RESPONSE_403_ADMIN
from src.schemas.tags import CreateTagRequest, UpdateTagRequest
from src.core.exceptions import AppError
from src.core.response import success_response
from src.sql.tags import TagRepository

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "",
    summary="태그 목록 조회",
    description="태그 목록을 조회합니다. 유형(category/region)으로 필터링하거나 이름으로 검색할 수 있습니다.",
)
def list_tags(
    request: Request,
    db: DbSession,
    type: str = Query(
        default="all",
        pattern="^(all|category|region)$",
        description="태그 유형 필터 (all, category, region)",
    ),
    search: str | None = Query(default=None, description="태그 이름 검색어"),
):
    repo = TagRepository(db)
    tags = repo.list_tags(tag_type=type, search=search)
    return success_response(
        request=request,
        data=[
            {
                "id": tag.id,
                "name": tag.name,
                "type": tag.type.value,
                "slug": tag.slug,
            }
            for tag in tags
        ],
        message="조회 성공",
    )


@router.post(
    "",
    summary="태그 생성 (관리자)",
    description="새 태그를 등록합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    status_code=201,
    responses={**RESPONSE_400, **RESPONSE_401, **RESPONSE_403_ADMIN},
)
def create_tag(
    payload: CreateTagRequest,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    repo = TagRepository(db)
    created = repo.create_tag(name=payload.name, tag_type=payload.type.value, slug=payload.slug)
    db.commit()
    return success_response(
        request=request,
        data={
            "id": created.id,
            "name": created.name,
            "type": created.type.value,
            "slug": created.slug,
            "createdAt": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
        },
        status_code=201,
        message="태그 생성 성공",
    )


@router.patch(
    "/{tag_id}",
    summary="태그 수정 (관리자)",
    description="태그 정보를 수정합니다. 변경할 필드만 전송합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "태그를 찾을 수 없음 (`E_RESOURCE_006`)", "model": ErrorResponse},
    },
)
def update_tag(
    tag_id: str,
    payload: UpdateTagRequest,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    repo = TagRepository(db)
    tag = repo.get_tag(tag_id)
    if tag is None:
        raise AppError(code="E_RESOURCE_006", message="태그를 찾을 수 없습니다.", status_code=404)

    updated = repo.update_tag(tag=tag, name=payload.name, slug=payload.slug)
    db.commit()
    return success_response(
        request=request,
        data={
            "id": updated.id,
            "name": updated.name,
            "type": updated.type.value,
            "slug": updated.slug,
            "updatedAt": updated.updated_at.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
        },
        message="태그 수정 성공",
    )


@router.delete(
    "/{tag_id}",
    summary="태그 삭제 (관리자)",
    description="태그를 삭제합니다. **관리자 권한 필요.** `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        **RESPONSE_403_ADMIN,
        404: {"description": "태그를 찾을 수 없음 (`E_RESOURCE_006`)", "model": ErrorResponse},
    },
)
def delete_tag(tag_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    repo = TagRepository(db)
    tag = repo.get_tag(tag_id)
    if tag is None:
        raise AppError(code="E_RESOURCE_006", message="태그를 찾을 수 없습니다.", status_code=404)

    repo.delete_tag(tag)
    db.commit()
    return success_response(request=request, data=None, message="태그 삭제 성공")
