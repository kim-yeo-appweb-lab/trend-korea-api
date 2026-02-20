from datetime import datetime, timezone

from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentAdminUserId, DbSession
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.tag_repository import TagRepository

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
def list_tags(
    request: Request,
    db: DbSession,
    type: str = Query(default="all", pattern="^(all|category|region)$"),
    search: str | None = Query(default=None),
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


@router.post("")
def create_tag(
    payload: dict,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    name = payload.get("name")
    tag_type = payload.get("type")
    slug = payload.get("slug")
    if not name or tag_type not in {"category", "region"} or not slug:
        raise AppError(code="E_VALID_001", message="필수 필드가 누락되었습니다.", status_code=400)

    repo = TagRepository(db)
    created = repo.create_tag(name=name, tag_type=tag_type, slug=slug)
    db.commit()
    return success_response(
        request=request,
        data={
            "id": created.id,
            "name": created.name,
            "type": created.type.value,
            "slug": created.slug,
            "createdAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        },
        status_code=201,
        message="태그 생성 성공",
    )


@router.patch("/{tag_id}")
def update_tag(
    tag_id: str,
    payload: dict,
    request: Request,
    db: DbSession,
    _: CurrentAdminUserId,
):
    repo = TagRepository(db)
    tag = repo.get_tag(tag_id)
    if tag is None:
        raise AppError(code="E_RESOURCE_006", message="태그를 찾을 수 없습니다.", status_code=404)

    updated = repo.update_tag(tag=tag, name=payload.get("name"), slug=payload.get("slug"))
    db.commit()
    return success_response(
        request=request,
        data={
            "id": updated.id,
            "name": updated.name,
            "type": updated.type.value,
            "slug": updated.slug,
            "updatedAt": updated.updated_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        },
        message="태그 수정 성공",
    )


@router.delete("/{tag_id}")
def delete_tag(tag_id: str, request: Request, db: DbSession, _: CurrentAdminUserId):
    repo = TagRepository(db)
    tag = repo.get_tag(tag_id)
    if tag is None:
        raise AppError(code="E_RESOURCE_006", message="태그를 찾을 수 없습니다.", status_code=404)

    repo.delete_tag(tag)
    db.commit()
    return success_response(request=request, data=None, message="태그 삭제 성공")
