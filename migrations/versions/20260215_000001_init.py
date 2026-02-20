"""init

Revision ID: 20260215_000001
Revises:
Create Date: 2026-02-15
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260215_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("nickname", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("profile_image", sa.String(length=500), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_nickname", "users", ["nickname"], unique=True)

    op.create_table(
        "user_social_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_user_id", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_social_accounts_user_id", "user_social_accounts", ["user_id"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tags_slug", "tags", ["slug"], unique=True)

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("importance", sa.String(length=20), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_occurred_at", "events", ["occurred_at"], unique=False)

    op.create_table(
        "issues",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("tracker_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latest_trigger_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_issues_status", "issues", ["status"], unique=False)
    op.create_index("ix_issues_tracker_count", "issues", ["tracker_count"], unique=False)
    op.create_index("ix_issues_latest_trigger_at", "issues", ["latest_trigger_at"], unique=False)

    op.create_table(
        "triggers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("issue_id", sa.String(length=36), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_triggers_issue_id", "triggers", ["issue_id"], unique=False)
    op.create_index("ix_triggers_occurred_at", "triggers", ["occurred_at"], unique=False)

    op.create_table(
        "posts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dislike_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_posts_author_id", "posts", ["author_id"], unique=False)
    op.create_index("ix_posts_created_at", "posts", ["created_at"], unique=False)

    op.create_table(
        "comments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("post_id", sa.String(length=36), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.String(length=36), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"], unique=False)
    op.create_index("ix_comments_created_at", "comments", ["created_at"], unique=False)

    op.create_table(
        "comment_likes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("comment_id", sa.String(length=36), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("comment_id", "user_id", name="uq_comment_like_user"),
    )
    op.create_index("ix_comment_likes_comment_id", "comment_likes", ["comment_id"], unique=False)
    op.create_index("ix_comment_likes_user_id", "comment_likes", ["user_id"], unique=False)

    op.create_table(
        "post_votes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("post_id", sa.String(length=36), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vote_type", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_vote_user"),
    )
    op.create_index("ix_post_votes_post_id", "post_votes", ["post_id"], unique=False)
    op.create_index("ix_post_votes_user_id", "post_votes", ["user_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)

    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("publisher", sa.String(length=100), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sources_entity_type", "sources", ["entity_type"], unique=False)
    op.create_index("ix_sources_entity_id", "sources", ["entity_id"], unique=False)

    op.create_table(
        "search_rankings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("keyword", sa.String(length=100), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_search_rankings_keyword", "search_rankings", ["keyword"], unique=False)
    op.create_index("ix_search_rankings_calculated_at", "search_rankings", ["calculated_at"], unique=False)

    op.create_table(
        "search_histories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("keyword", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_search_histories_user_id", "search_histories", ["user_id"], unique=False)
    op.create_index("ix_search_histories_created_at", "search_histories", ["created_at"], unique=False)

    op.create_table(
        "job_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_job_runs_job_name", "job_runs", ["job_name"], unique=False)

    op.create_table(
        "event_tags",
        sa.Column("event_id", sa.String(length=36), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(length=36), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_saved_events",
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", sa.String(length=36), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "issue_tags",
        sa.Column("issue_id", sa.String(length=36), sa.ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(length=36), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "issue_events",
        sa.Column("issue_id", sa.String(length=36), sa.ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", sa.String(length=36), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_tracked_issues",
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("issue_id", sa.String(length=36), sa.ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tracked_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "post_tags",
        sa.Column("post_id", sa.String(length=36), sa.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(length=36), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("post_tags")
    op.drop_table("user_tracked_issues")
    op.drop_table("issue_events")
    op.drop_table("issue_tags")
    op.drop_table("user_saved_events")
    op.drop_table("event_tags")

    op.drop_index("ix_job_runs_job_name", table_name="job_runs")
    op.drop_table("job_runs")

    op.drop_index("ix_search_histories_created_at", table_name="search_histories")
    op.drop_index("ix_search_histories_user_id", table_name="search_histories")
    op.drop_table("search_histories")

    op.drop_index("ix_search_rankings_calculated_at", table_name="search_rankings")
    op.drop_index("ix_search_rankings_keyword", table_name="search_rankings")
    op.drop_table("search_rankings")

    op.drop_index("ix_sources_entity_id", table_name="sources")
    op.drop_index("ix_sources_entity_type", table_name="sources")
    op.drop_table("sources")

    op.drop_index("ix_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_post_votes_user_id", table_name="post_votes")
    op.drop_index("ix_post_votes_post_id", table_name="post_votes")
    op.drop_table("post_votes")

    op.drop_index("ix_comment_likes_user_id", table_name="comment_likes")
    op.drop_index("ix_comment_likes_comment_id", table_name="comment_likes")
    op.drop_table("comment_likes")

    op.drop_index("ix_comments_created_at", table_name="comments")
    op.drop_index("ix_comments_post_id", table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_posts_created_at", table_name="posts")
    op.drop_index("ix_posts_author_id", table_name="posts")
    op.drop_table("posts")

    op.drop_index("ix_triggers_occurred_at", table_name="triggers")
    op.drop_index("ix_triggers_issue_id", table_name="triggers")
    op.drop_table("triggers")

    op.drop_index("ix_issues_latest_trigger_at", table_name="issues")
    op.drop_index("ix_issues_tracker_count", table_name="issues")
    op.drop_index("ix_issues_status", table_name="issues")
    op.drop_table("issues")

    op.drop_index("ix_events_occurred_at", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_tags_slug", table_name="tags")
    op.drop_table("tags")

    op.drop_index("ix_user_social_accounts_user_id", table_name="user_social_accounts")
    op.drop_table("user_social_accounts")

    op.drop_index("ix_users_nickname", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
