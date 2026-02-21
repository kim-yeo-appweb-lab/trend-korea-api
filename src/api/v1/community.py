from fastapi import APIRouter, Query, Request

from src.utils.dependencies import CurrentMemberUserId, DbSession
from src.schemas.shared import ErrorResponse, RESPONSE_400, RESPONSE_401, RESPONSE_403_OWNER
from src.schemas.community import (
    CreateCommentRequest,
    CreatePostRequest,
    UpdateCommentRequest,
    UpdatePostRequest,
    VoteRequest,
)
from src.crud.community import CommunityService
from src.core.exceptions import AppError
from src.core.response import success_response
from src.db.enums import VoteType
from src.sql.community import CommunityRepository

router = APIRouter(tags=["posts", "comments"])


@router.get(
    "/posts",
    summary="게시글 목록 조회",
    description="커서 기반 페이지네이션으로 게시글 목록을 조회합니다. 탭(최신/인기)과 정렬 기준을 지정할 수 있습니다.",
)
def list_posts(
    request: Request,
    db: DbSession,
    cursor: str | None = Query(default=None, description="다음 페이지 커서 토큰"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 항목 수"),
    tab: str = Query(default="latest", description="탭 필터 (latest: 최신, popular: 인기)"),
    sortBy: str = Query(default="createdAt", description="정렬 기준 필드"),
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


@router.post(
    "/posts",
    summary="게시글 작성",
    description="새 게시글을 작성합니다. 태그는 최대 3개까지 지정 가능합니다. `Authorization: Bearer <token>` 필요.",
    status_code=201,
    responses={**RESPONSE_400, **RESPONSE_401},
)
def create_post(
    payload: CreatePostRequest, request: Request, db: DbSession, user_id: CurrentMemberUserId
):
    service = CommunityService(CommunityRepository(db))
    if len(payload.tagIds) > 3:
        raise AppError(
            code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400
        )

    created = service.create_post(
        user_id=user_id,
        title=payload.title,
        content=payload.content,
        is_anonymous=payload.isAnonymous,
        tag_ids=payload.tagIds,
    )
    db.commit()
    return success_response(
        request=request, data=created, status_code=201, message="게시글 생성 성공"
    )


@router.get(
    "/posts/{post_id}",
    summary="게시글 상세 조회",
    description="게시글 ID로 상세 정보를 조회합니다. 작성자, 태그, 추천 수, 댓글 수를 포함합니다.",
    responses={
        404: {"description": "게시글을 찾을 수 없음 (`E_RESOURCE_003`)", "model": ErrorResponse},
    },
)
def get_post(post_id: str, request: Request, db: DbSession):
    service = CommunityService(CommunityRepository(db))
    item = service.get_post(post_id)
    if item is None:
        raise AppError(code="E_RESOURCE_003", message="게시글을 찾을 수 없습니다.", status_code=404)
    return success_response(request=request, data=item, message="조회 성공")


@router.patch(
    "/posts/{post_id}",
    summary="게시글 수정",
    description="게시글을 수정합니다. 작성자 본인 또는 관리자만 가능합니다. 변경할 필드만 전송합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        **RESPONSE_403_OWNER,
    },
)
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
        raise AppError(
            code="E_VALID_002", message="tagIds는 최대 3개까지 허용됩니다.", status_code=400
        )

    updated = service.update_post(
        post_id=post_id,
        user_id=user_id,
        title=payload.title,
        content=payload.content,
        tag_ids=payload.tagIds,
        is_admin=is_admin,
    )
    db.commit()
    return success_response(request=request, data=updated, message="게시글 수정 성공")


@router.delete(
    "/posts/{post_id}",
    summary="게시글 삭제",
    description="게시글을 삭제합니다. 작성자 본인 또는 관리자만 가능합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        **RESPONSE_403_OWNER,
    },
)
def delete_post(post_id: str, request: Request, db: DbSession, user_id: CurrentMemberUserId):
    service = CommunityService(CommunityRepository(db))
    is_admin = getattr(request.state, "user_role", None) == "admin"
    service.delete_post(post_id=post_id, user_id=user_id, is_admin=is_admin)
    db.commit()
    return success_response(request=request, data=None, message="게시글 삭제 성공")


@router.get(
    "/posts/{post_id}/comments",
    summary="댓글 목록 조회",
    description="특정 게시글의 댓글 목록을 커서 기반 페이지네이션으로 조회합니다. 대댓글은 parentId로 구분됩니다.",
)
def list_comments(
    post_id: str,
    request: Request,
    db: DbSession,
    cursor: str | None = Query(default=None, description="다음 페이지 커서 토큰"),
    limit: int = Query(default=20, ge=1, le=100, description="한 페이지에 조회할 댓글 수"),
):
    service = CommunityService(CommunityRepository(db))
    items, _ = service.list_comments(post_id=post_id, size=limit, cursor=cursor)
    return success_response(
        request=request,
        data=items,
        message="조회 성공",
    )


@router.post(
    "/posts/{post_id}/comments",
    summary="댓글 작성",
    description="게시글에 댓글을 작성합니다. parentId를 지정하면 대댓글이 됩니다. `Authorization: Bearer <token>` 필요.",
    status_code=201,
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        404: {"description": "게시글을 찾을 수 없음 (`E_RESOURCE_003`)", "model": ErrorResponse},
    },
)
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


@router.post(
    "/posts/{post_id}/like",
    summary="게시글 추천/비추천",
    description="게시글에 추천(like) 또는 비추천(dislike)을 합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        404: {"description": "게시글을 찾을 수 없음 (`E_RESOURCE_003`)", "model": ErrorResponse},
    },
)
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
        raise AppError(
            code="E_VALID_002", message="type은 like 또는 dislike 여야 합니다.", status_code=400
        ) from exc
    result = service.vote_post(post_id=post_id, user_id=user_id, vote_type=vote_type)
    if result is None:
        raise AppError(code="E_RESOURCE_003", message="게시글을 찾을 수 없습니다.", status_code=404)
    db.commit()
    return success_response(request=request, data=result, message="추천 성공")


@router.patch(
    "/comments/{comment_id}",
    summary="댓글 수정",
    description="댓글을 수정합니다. 작성자 본인 또는 관리자만 가능합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_400,
        **RESPONSE_401,
        **RESPONSE_403_OWNER,
    },
)
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
    db.commit()
    return success_response(
        request=request,
        data={"id": item["id"], "content": item["content"], "updatedAt": item["updatedAt"]},
        message="댓글 수정 성공",
    )


@router.delete(
    "/comments/{comment_id}",
    summary="댓글 삭제",
    description="댓글을 삭제합니다. 작성자 본인 또는 관리자만 가능합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        **RESPONSE_403_OWNER,
    },
)
def delete_comment(
    comment_id: str,
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
):
    service = CommunityService(CommunityRepository(db))
    is_admin = getattr(request.state, "user_role", None) == "admin"
    service.delete_comment(comment_id=comment_id, user_id=user_id, is_admin=is_admin)
    db.commit()
    return success_response(request=request, data=None, message="댓글 삭제 성공")


@router.post(
    "/comments/{comment_id}/like",
    summary="댓글 좋아요",
    description="댓글에 좋아요를 표시합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        404: {"description": "댓글을 찾을 수 없음 (`E_RESOURCE_004`)", "model": ErrorResponse},
    },
)
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


@router.delete(
    "/comments/{comment_id}/like",
    summary="댓글 좋아요 취소",
    description="댓글의 좋아요를 취소합니다. `Authorization: Bearer <token>` 필요.",
    responses={
        **RESPONSE_401,
        404: {"description": "댓글을 찾을 수 없음 (`E_RESOURCE_004`)", "model": ErrorResponse},
    },
)
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
