from src.core.exceptions import AppError
from src.core.pagination import decode_cursor, encode_cursor
from src.db.enums import VoteType
from src.sql.community import CommunityRepository


class CommunityService:
    def __init__(self, repository: CommunityRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_iso(dt) -> str | None:
        if dt is None:
            return None
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @staticmethod
    def _comment_to_item(comment) -> dict:
        return {
            "id": comment.id,
            "postId": comment.post_id,
            "parentId": comment.parent_id,
            "authorId": comment.author_id,
            "authorNickname": None,
            "content": comment.content,
            "likeCount": comment.like_count,
            "createdAt": CommunityService._to_iso(comment.created_at),
            "updatedAt": CommunityService._to_iso(comment.updated_at),
        }

    def list_posts(
        self,
        *,
        tab: str,
        sort: str,
        size: int,
        cursor: str | None,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        items, next_offset = self.repository.list_posts(
            tab=tab, sort=sort, size=size, offset=offset
        )
        return [self._post_to_item(post) for post in items], encode_cursor(
            next_offset
        ) if next_offset is not None else None

    def get_post(self, post_id: str) -> dict | None:
        post = self.repository.get_post(post_id)
        if post is None:
            return None
        return self._post_to_item(post)

    def create_post(
        self,
        *,
        user_id: str,
        title: str,
        content: str,
        is_anonymous: bool,
        tag_ids: list[str],
    ) -> dict:
        post = self.repository.create_post(
            author_id=user_id,
            title=title,
            content=content,
            is_anonymous=is_anonymous,
            tag_ids=tag_ids,
        )
        return self._post_to_item(post)

    def update_post(
        self,
        *,
        post_id: str,
        user_id: str,
        title: str | None,
        content: str | None,
        tag_ids: list[str] | None,
        is_admin: bool = False,
    ) -> dict:
        post = self.repository.get_post(post_id)
        if post is None:
            raise AppError(
                code="E_RESOURCE_003", message="게시글을 찾을 수 없습니다.", status_code=404
            )
        if post.author_id != user_id and not is_admin:
            raise AppError(
                code="E_PERM_001", message="작성자 또는 관리자만 가능합니다.", status_code=403
            )
        updated = self.repository.update_post(
            post=post, title=title, content=content, tag_ids=tag_ids
        )
        return self._post_to_item(updated)

    def delete_post(self, *, post_id: str, user_id: str, is_admin: bool = False) -> None:
        post = self.repository.get_post(post_id)
        if post is None:
            raise AppError(
                code="E_RESOURCE_003", message="게시글을 찾을 수 없습니다.", status_code=404
            )
        if post.author_id != user_id and not is_admin:
            raise AppError(
                code="E_PERM_001", message="작성자 또는 관리자만 가능합니다.", status_code=403
            )
        self.repository.delete_post(post)

    def list_comments(
        self,
        *,
        post_id: str,
        size: int,
        cursor: str | None,
    ) -> tuple[list[dict], str | None]:
        offset = decode_cursor(cursor)
        comments, next_offset = self.repository.list_comments(
            post_id=post_id, size=size, offset=offset
        )
        return [self._comment_to_item(comment) for comment in comments], encode_cursor(
            next_offset
        ) if next_offset is not None else None

    def create_comment(
        self,
        *,
        post_id: str,
        user_id: str,
        content: str,
        parent_id: str | None,
    ) -> dict | None:
        post = self.repository.get_post(post_id)
        if post is None:
            return None
        if parent_id:
            parent = self.repository.get_comment(parent_id)
            if parent is None:
                raise AppError(
                    code="E_RESOURCE_004",
                    message="부모 댓글을 찾을 수 없습니다.",
                    status_code=404,
                )
            if parent.post_id != post_id:
                raise AppError(
                    code="E_VALID_002",
                    message="다른 게시글의 댓글에는 대댓글을 달 수 없습니다.",
                    status_code=400,
                )
        comment = self.repository.create_comment(
            post=post,
            author_id=user_id,
            content=content,
            parent_id=parent_id,
        )
        return self._comment_to_item(comment)

    def update_comment(
        self, *, comment_id: str, user_id: str, content: str, is_admin: bool = False
    ) -> dict:
        comment = self.repository.get_comment(comment_id)
        if comment is None:
            raise AppError(
                code="E_RESOURCE_004", message="댓글을 찾을 수 없습니다.", status_code=404
            )
        if comment.author_id != user_id and not is_admin:
            raise AppError(
                code="E_PERM_001", message="작성자 또는 관리자만 가능합니다.", status_code=403
            )
        updated = self.repository.update_comment(comment=comment, content=content)
        return self._comment_to_item(updated)

    def delete_comment(self, *, comment_id: str, user_id: str, is_admin: bool = False) -> None:
        comment = self.repository.get_comment(comment_id)
        if comment is None:
            raise AppError(
                code="E_RESOURCE_004", message="댓글을 찾을 수 없습니다.", status_code=404
            )
        if comment.author_id != user_id and not is_admin:
            raise AppError(
                code="E_PERM_001", message="작성자 또는 관리자만 가능합니다.", status_code=403
            )
        self.repository.delete_comment(comment=comment)

    def like_comment(self, *, comment_id: str, user_id: str) -> dict | None:
        comment = self.repository.get_comment(comment_id)
        if comment is None:
            return None
        updated, _ = self.repository.like_comment(comment=comment, user_id=user_id)
        return {
            "commentId": updated.id,
            "likeCount": updated.like_count,
            "userLiked": True,
        }

    def unlike_comment(self, *, comment_id: str, user_id: str) -> dict | None:
        comment = self.repository.get_comment(comment_id)
        if comment is None:
            return None
        updated, _ = self.repository.unlike_comment(comment=comment, user_id=user_id)
        return {
            "commentId": updated.id,
            "likeCount": updated.like_count,
            "userLiked": False,
        }

    def vote_post(self, *, post_id: str, user_id: str, vote_type: VoteType) -> dict | None:
        post = self.repository.get_post(post_id)
        if post is None:
            return None
        vote = self.repository.vote_post(post=post, user_id=user_id, vote_type=vote_type)
        return {
            "postId": post.id,
            "type": vote.vote_type,
            "likeCount": post.like_count,
            "dislikeCount": post.dislike_count,
            "userAction": vote.vote_type,
        }

    @staticmethod
    def _post_to_item(post) -> dict:
        return {
            "id": post.id,
            "authorId": post.author_id,
            "authorNickname": None,
            "authorImage": None,
            "title": post.title,
            "content": post.content,
            "tags": [],
            "isAnonymous": post.is_anonymous,
            "likeCount": post.like_count,
            "dislikeCount": post.dislike_count,
            "commentCount": post.comment_count,
            "createdAt": CommunityService._to_iso(post.created_at),
            "updatedAt": CommunityService._to_iso(post.updated_at),
        }
