from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import asc, delete, desc, insert, select
from sqlalchemy.orm import Session

from trend_korea.domain.enums import VoteType
from trend_korea.infrastructure.db.models.community import Comment, CommentLike, Post, PostVote, post_tags


class CommunityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _apply_sort(self, stmt, *, tab: str, sort: str):
        hot_score = (Post.like_count - Post.dislike_count) * 2 + Post.comment_count

        if tab == "popular":
            return stmt.order_by(desc(Post.like_count), desc(Post.created_at))
        if tab == "hot":
            return stmt.order_by(desc(hot_score), desc(Post.created_at))

        sort_map = {
            "createdAt": Post.created_at,
            "likeScore": Post.like_count,
            "commentCount": Post.comment_count,
        }
        orders = []
        for token in [v.strip() for v in sort.split(",") if v.strip()]:
            desc_mode = token.startswith("-")
            key = token[1:] if desc_mode else token
            column = sort_map.get(key)
            if not column:
                continue
            orders.append(desc(column) if desc_mode else asc(column))
        if not orders:
            orders = [desc(Post.created_at)]
        return stmt.order_by(*orders)

    def list_posts(
        self,
        *,
        tab: str,
        sort: str,
        size: int,
        offset: int,
    ) -> tuple[list[Post], int | None]:
        stmt = select(Post)
        stmt = self._apply_sort(stmt, tab=tab, sort=sort)
        rows = self.db.execute(stmt.offset(offset).limit(size + 1)).scalars().all()
        has_next = len(rows) > size
        items = rows[:size]
        next_offset = offset + size if has_next else None
        return items, next_offset

    def get_post(self, post_id: str) -> Post | None:
        stmt = select(Post).where(Post.id == post_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_post(
        self,
        *,
        author_id: str,
        title: str,
        content: str,
        is_anonymous: bool,
        tag_ids: list[str],
    ) -> Post:
        now = datetime.now(timezone.utc)
        post = Post(
            id=str(uuid4()),
            author_id=author_id,
            title=title,
            content=content,
            is_anonymous=is_anonymous,
            created_at=now,
            updated_at=now,
        )
        self.db.add(post)
        self.db.flush()

        if tag_ids:
            self.db.execute(
                insert(post_tags),
                [{"post_id": post.id, "tag_id": tag_id} for tag_id in tag_ids],
            )
        self.db.flush()
        return post

    def update_post(
        self,
        *,
        post: Post,
        title: str | None,
        content: str | None,
        tag_ids: list[str] | None,
    ) -> Post:
        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        if tag_ids is not None:
            self.db.execute(delete(post_tags).where(post_tags.c.post_id == post.id))
            if tag_ids:
                self.db.execute(
                    insert(post_tags),
                    [{"post_id": post.id, "tag_id": tag_id} for tag_id in tag_ids],
                )
        post.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return post

    def delete_post(self, post: Post) -> None:
        self.db.delete(post)
        self.db.flush()

    def list_comments(
        self,
        *,
        post_id: str,
        size: int,
        offset: int,
    ) -> tuple[list[Comment], int | None]:
        stmt = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(asc(Comment.created_at))
        )
        rows = self.db.execute(stmt.offset(offset).limit(size + 1)).scalars().all()
        has_next = len(rows) > size
        items = rows[:size]
        next_offset = offset + size if has_next else None
        return items, next_offset

    def get_comment(self, comment_id: str) -> Comment | None:
        stmt = select(Comment).where(Comment.id == comment_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_comment(
        self,
        *,
        post: Post,
        author_id: str,
        content: str,
        parent_id: str | None,
    ) -> Comment:
        now = datetime.now(timezone.utc)
        comment = Comment(
            id=str(uuid4()),
            post_id=post.id,
            parent_id=parent_id,
            author_id=author_id,
            content=content,
            created_at=now,
            updated_at=now,
        )
        self.db.add(comment)
        post.comment_count += 1
        self.db.flush()
        return comment

    def update_comment(self, *, comment: Comment, content: str) -> Comment:
        comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return comment

    def delete_comment(self, *, comment: Comment) -> None:
        post = self.get_post(comment.post_id)
        self.db.delete(comment)
        if post and post.comment_count > 0:
            post.comment_count -= 1
        self.db.flush()

    def like_comment(self, *, comment: Comment, user_id: str) -> tuple[Comment, bool]:
        stmt = select(CommentLike).where(CommentLike.comment_id == comment.id, CommentLike.user_id == user_id)
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing is not None:
            return comment, False

        like = CommentLike(
            id=str(uuid4()),
            comment_id=comment.id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(like)
        comment.like_count += 1
        self.db.flush()
        return comment, True

    def unlike_comment(self, *, comment: Comment, user_id: str) -> tuple[Comment, bool]:
        stmt = select(CommentLike).where(CommentLike.comment_id == comment.id, CommentLike.user_id == user_id)
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing is None:
            return comment, False

        self.db.delete(existing)
        if comment.like_count > 0:
            comment.like_count -= 1
        self.db.flush()
        return comment, True

    def vote_post(self, *, post: Post, user_id: str, vote_type: VoteType) -> PostVote:
        stmt = select(PostVote).where(PostVote.post_id == post.id, PostVote.user_id == user_id)
        existing = self.db.execute(stmt).scalar_one_or_none()

        if existing is None:
            vote = PostVote(
                id=str(uuid4()),
                post_id=post.id,
                user_id=user_id,
                vote_type=vote_type.value,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(vote)
            if vote_type == VoteType.LIKE:
                post.like_count += 1
            else:
                post.dislike_count += 1
            self.db.flush()
            return vote

        if existing.vote_type == vote_type.value:
            return existing

        if existing.vote_type == VoteType.LIKE.value:
            post.like_count = max(post.like_count - 1, 0)
        else:
            post.dislike_count = max(post.dislike_count - 1, 0)

        existing.vote_type = vote_type.value
        if vote_type == VoteType.LIKE:
            post.like_count += 1
        else:
            post.dislike_count += 1

        self.db.flush()
        return existing
