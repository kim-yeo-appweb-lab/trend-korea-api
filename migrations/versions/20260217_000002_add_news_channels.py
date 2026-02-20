"""add news_channels table

Revision ID: 20260217_000002
Revises: 20260215_000001
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260217_000002"
down_revision = "20260215_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_channels",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_news_channels_code", "news_channels", ["code"], unique=True)
    op.create_index("ix_news_channels_symbol", "news_channels", ["symbol"], unique=True)
    op.create_index("ix_news_channels_category", "news_channels", ["category"], unique=False)
    op.create_index("ix_news_channels_is_active", "news_channels", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_news_channels_is_active", table_name="news_channels")
    op.drop_index("ix_news_channels_category", table_name="news_channels")
    op.drop_index("ix_news_channels_symbol", table_name="news_channels")
    op.drop_index("ix_news_channels_code", table_name="news_channels")
    op.drop_table("news_channels")
