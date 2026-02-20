"""add crawled_keywords table

Revision ID: 20260217_000003
Revises: 20260217_000002
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260217_000003"
down_revision = "20260217_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crawled_keywords",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("keyword", sa.String(length=100), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("channel_code", sa.String(length=20), nullable=True),
        sa.Column("channel_name", sa.String(length=50), nullable=True),
        sa.Column("category", sa.String(length=20), nullable=True),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_crawled_keywords_keyword", "crawled_keywords", ["keyword"])
    op.create_index("ix_crawled_keywords_channel_code", "crawled_keywords", ["channel_code"])
    op.create_index("ix_crawled_keywords_source_type", "crawled_keywords", ["source_type"])
    op.create_index("ix_crawled_keywords_crawled_at", "crawled_keywords", ["crawled_at"])


def downgrade() -> None:
    op.drop_index("ix_crawled_keywords_crawled_at", table_name="crawled_keywords")
    op.drop_index("ix_crawled_keywords_source_type", table_name="crawled_keywords")
    op.drop_index("ix_crawled_keywords_channel_code", table_name="crawled_keywords")
    op.drop_index("ix_crawled_keywords_keyword", table_name="crawled_keywords")
    op.drop_table("crawled_keywords")
