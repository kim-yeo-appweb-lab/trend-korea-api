from fastapi import APIRouter, Query, Request

from trend_korea.api.deps import CurrentMemberUserId, DbSession
from trend_korea.api.schemas.community import (
    CreateCommentRequest,
    CreatePostRequest,
    UpdateCommentRequest,
    UpdatePostRequest,
    VoteRequest,
)
from trend_korea.application.community.service import CommunityService
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.domain.enums import VoteType
from trend_korea.infrastructure.db.repositories.community_repository import CommunityRepository

router = APIRouter(tags=["posts", "comments"])


@router.get("/posts")
def list_posts(
    request: Request,
    db: DbSession,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    tab: str = Query(default="latest"),
    sortBy: str = Query(default="createdAt"),
):
    service = CommunityService(CommunityRepository(db))
    sort = f"-{sortBy}"
    items, next_cursor = service.list_posts(tab=tab, sort=sort, size=limit, cursor=cursor)

    return success_response(
        request=request,
        data={
            "items": items,
            "cursor": {
                "next": next_cursor,
                "hasMore": next_cursor is not None,
            },
        },
        message="조회 성공",
    )


@router.post("/posts")
def create_post(payload: CreatePostRequest, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = CommunityService(CommunityRepository(db))
    if len(payload.tagIds) > 3:
        raise AppError(code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400)

    created = service.create_post(
        user_id=user_id,
        title=payload.title,
        content=payload.content,
        is_anonymous=payload.isAnonymous,
        tag_ids=payload.tagIds,
    )
    db.commit()
    return success_response(request=request, data=created, status_code=201, message="게시글 생성 성공")


@router.get("/posts/{post_id}")
def get_post(post_id: str, request: Request, db: DbSession):
    service = CommunityService(CommunityRepository(db))
    item = service.get_post(post_id)
    if item is None:
        raise AppError(code="E_RESOURCE_003", message="게시글을 찾을 수 없습니다.", status_code=404)
    return success_response(request=request, data=item, message="조회 성공")


@router.patch("/posts/{post_id}")
def update_post(
    post_id: str,
    payload: UpdatePostRequest,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    is_admin = getattr(request.state, "user_role", None) == "admin"
    if payload.tagIds is not None and len(payload.tagIds) > 3:
        raise AppError(code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400)

    updated = service.update_post(
        post_id=post_id,
        user_id=user_id,
        title=payload.title,
        content=payload.content,
        tag_ids=payload.tagIds,
        is_admin=is_admin,
    )
    if updated is None:
        raise AppError(code="E_PERM_001", message="작성자가 아닙니다.", status_code=403)
    db.commit()
    return success_response(request=request, data=updated, message="게시글 수정 성공")


@router.delete("/posts/{post_id}")
def delete_post(post_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = CommunityService(CommunityRepository(db))
    is_admin = getattr(request.state, "user_role", None) == "admin"
    ok = service.delete_post(post_id=post_id, user_id=user_id, is_admin=is_admin)
    if not ok:
        raise AppError(code="E_PERM_001", message="작성자가 아닙니다.", status_code=403)
    db.commit()
    return success_response(request=request, data=None, message="게시글 삭제 성공")


@router.get("/posts/{post_id}/comments")
def list_comments(
    post_id: str,
    request: Request,
    db: DbSession,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    service = CommunityService(CommunityRepository(db))
    items, _ = service.list_comments(post_id=post_id, size=limit, cursor=cursor)
    return success_response(
        request=request,
        data=items,
        message="조회 성공",
    )


@router.post("/posts/{post_id}/comments")
def create_comment(
    post_id: str,
    payload: CreateCommentRequest,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    item = service.create_comment(
        post_id=post_id,
        user_id=user_id,
        content=payload.content,
        parent_id=payload.parentId,
    )
    if item is None:
        raise AppError(code="E_RESOURCE_003", message="게시글을 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=item, status_code=201, message="댓글 생성 성공")


@router.post("/posts/{post_id}/like")
def vote_post(
    post_id: str,
    payload: VoteRequest,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    try:
        vote_type = VoteType(payload.type)
    except ValueError as exc:
        raise AppError(code="E_VALID_002", message="type은 like 또는 dislike 여야 합니다.", status_code=400) from exc
    result = service.vote_post(post_id=post_id, user_id=user_id, vote_type=vote_type)
    if result is None:
        raise AppError(code="E_RESOURCE_003", message="게시글을 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=result, message="추천 성공")


@router.patch("/comments/{comment_id}")
def update_comment(
    comment_id: str,
    payload: UpdateCommentRequest,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    is_admin = getattr(request.state, "user_role", None) == "admin"
    item = service.update_comment(
        comment_id=comment_id,
        user_id=user_id,
        content=payload.content,
        is_admin=is_admin,
    )
    if item is None:
        raise AppError(code="E_PERM_001", message="작성자가 아닙니다.", status_code=403)
    db.commit()
    return success_response(
        request=request,
        data={"id": item["id"], "content": item["content"], "updatedAt": item["updatedAt"]},
        message="댓글 수정 성공",
    )


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: str,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    is_admin = getattr(request.state, "user_role", None) == "admin"
    ok = service.delete_comment(comment_id=comment_id, user_id=user_id, is_admin=is_admin)
    if not ok:
        raise AppError(code="E_PERM_001", message="작성자가 아닙니다.", status_code=403)
    db.commit()
    return success_response(request=request, data=None, message="댓글 삭제 성공")


@router.post("/comments/{comment_id}/like")
def like_comment(
    comment_id: str,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    result = service.like_comment(comment_id=comment_id, user_id=user_id)
    if result is None:
        raise AppError(code="E_RESOURCE_004", message="댓글을 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=result, message="좋아요 성공")


@router.delete("/comments/{comment_id}/like")
def unlike_comment(
    comment_id: str,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    result = service.unlike_comment(comment_id=comment_id, user_id=user_id)
    if result is None:
        raise AppError(code="E_RESOURCE_004", message="댓글을 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=result, message="좋아요 취소 성공")
