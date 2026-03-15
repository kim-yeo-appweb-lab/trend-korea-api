from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.orm import Session

from src.models.community import Comment, Post, PostVote
from src.models.events import user_saved_events
from src.models.issues import user_tracked_issues
from src.models.users import User, UserSocialAccount


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_nickname(self, nickname: str) -> User | None:
        stmt = select(User).where(User.nickname == nickname)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_profile(
        self,
        user: User,
        *,
        nickname: str | None,
        profile_image: str | None,
    ) -> User:
        if nickname is not None:
            user.nickname = nickname
        if profile_image is not None:
            user.profile_image = profile_image
        user.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return user

    def get_social_providers(self, user_id: str) -> list[str]:
        stmt = select(UserSocialAccount.provider).where(
            UserSocialAccount.user_id == user_id
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_tracked_issue_ids(self, user_id: str) -> list[str]:
        stmt = select(user_tracked_issues.c.issue_id).where(
            user_tracked_issues.c.user_id == user_id
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_saved_event_ids(self, user_id: str) -> list[str]:
        stmt = select(user_saved_events.c.event_id).where(
            user_saved_events.c.user_id == user_id
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_activity_stats(self, user_id: str) -> dict[str, int]:
        post_count = self.db.execute(
            select(func.count()).where(Post.author_id == user_id)
        ).scalar_one()
        comment_count = self.db.execute(
            select(func.count()).where(Comment.author_id == user_id)
        ).scalar_one()
        like_count = self.db.execute(
            select(func.count()).where(PostVote.user_id == user_id)
        ).scalar_one()
        return {
            "postCount": post_count,
            "commentCount": comment_count,
            "likeCount": like_count,
        }

    def get_activity(
        self,
        user_id: str,
        activity_type: str,
        offset: int,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        queries = []

        if activity_type in ("all", "post"):
            queries.append(
                select(
                    Post.id.label("target_id"),
                    Post.title.label("title"),
                    Post.created_at.label("created_at"),
                    literal("post").label("type"),
                ).where(Post.author_id == user_id)
            )

        if activity_type in ("all", "comment"):
            queries.append(
                select(
                    Comment.id.label("target_id"),
                    Comment.content.label("title"),
                    Comment.created_at.label("created_at"),
                    literal("comment").label("type"),
                ).where(Comment.author_id == user_id)
            )

        if activity_type in ("all", "like"):
            queries.append(
                select(
                    PostVote.post_id.label("target_id"),
                    literal("").label("title"),
                    PostVote.created_at.label("created_at"),
                    literal("like").label("type"),
                ).where(PostVote.user_id == user_id)
            )

        if not queries:
            return [], 0

        combined = union_all(*queries).subquery()

        total = self.db.execute(
            select(func.count()).select_from(combined)
        ).scalar_one()

        rows = self.db.execute(
            select(combined)
            .order_by(combined.c.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        items = [
            {
                "type": row.type,
                "targetId": row.target_id,
                "title": row.title,
                "createdAt": row.created_at.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                ),
            }
            for row in rows
        ]
        return items, total
