"""뉴스 요약 테이블 추가 (batches, summaries, tags)

Revision ID: a27b8d1a6e1a
Revises: 20260217_000003
Create Date: 2026-02-23 13:13:40.659737
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a27b8d1a6e1a'
down_revision = '20260217_000003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('news_summary_batches',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('provider', sa.String(length=30), nullable=False),
    sa.Column('model', sa.String(length=60), nullable=False),
    sa.Column('total_keywords', sa.Integer(), nullable=False),
    sa.Column('total_articles', sa.Integer(), nullable=False),
    sa.Column('prompt_tokens', sa.Integer(), nullable=False),
    sa.Column('completion_tokens', sa.Integer(), nullable=False),
    sa.Column('summarized_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_summary_batches_summarized_at'), 'news_summary_batches', ['summarized_at'], unique=False)

    op.create_table('news_keyword_summaries',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('batch_id', sa.String(length=36), nullable=False),
    sa.Column('keyword', sa.String(length=100), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('key_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('sentiment', sa.String(length=20), nullable=False),
    sa.Column('category', sa.String(length=30), nullable=False),
    sa.Column('article_count', sa.Integer(), nullable=False),
    sa.Column('articles', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['news_summary_batches.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_keyword_summaries_batch_id'), 'news_keyword_summaries', ['batch_id'], unique=False)
    op.create_index(op.f('ix_news_keyword_summaries_keyword'), 'news_keyword_summaries', ['keyword'], unique=False)
    op.create_index('ix_nks_category', 'news_keyword_summaries', ['category'], unique=False)
    op.create_index('ix_nks_keyword_created', 'news_keyword_summaries', ['keyword', 'created_at'], unique=False)
    op.create_index('ix_nks_sentiment', 'news_keyword_summaries', ['sentiment'], unique=False)

    op.create_table('news_summary_tags',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('summary_id', sa.String(length=36), nullable=False),
    sa.Column('tag', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['summary_id'], ['news_keyword_summaries.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_nst_summary_tag', 'news_summary_tags', ['summary_id', 'tag'], unique=True)
    op.create_index('ix_nst_tag', 'news_summary_tags', ['tag'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_nst_tag', table_name='news_summary_tags')
    op.drop_index('ix_nst_summary_tag', table_name='news_summary_tags')
    op.drop_table('news_summary_tags')
    op.drop_index('ix_nks_sentiment', table_name='news_keyword_summaries')
    op.drop_index('ix_nks_keyword_created', table_name='news_keyword_summaries')
    op.drop_index('ix_nks_category', table_name='news_keyword_summaries')
    op.drop_index(op.f('ix_news_keyword_summaries_keyword'), table_name='news_keyword_summaries')
    op.drop_index(op.f('ix_news_keyword_summaries_batch_id'), table_name='news_keyword_summaries')
    op.drop_table('news_keyword_summaries')
    op.drop_index(op.f('ix_news_summary_batches_summarized_at'), table_name='news_summary_batches')
    op.drop_table('news_summary_batches')
