from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.community import Comment, Post


def recalculate_community_hot_score(db: Session) -> str:
    posts = db.execute(select(Post)).scalars().all()
    updated = 0

    for post in posts:
        comment_count = db.execute(
            select(func.count(Comment.id)).where(Comment.post_id == post.id)
        ).scalar_one()

        if post.comment_count != comment_count:
            post.comment_count = int(comment_count)
            updated += 1

    return f"posts_updated={updated}"
