"""feat(db): 뉴스 분류 시스템 신규 테이블 추가

Revision ID: c1ffbc23a48a
Revises: 24b659aec956
Create Date: 2026-03-03 16:37:38.868035
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1ffbc23a48a'
down_revision = '24b659aec956'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. raw_articles
    op.create_table('raw_articles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('canonical_url', sa.String(length=2000), nullable=False),
        sa.Column('original_url', sa.String(length=2000), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('source_name', sa.String(length=100), nullable=True),
        sa.Column('title_hash', sa.String(length=64), nullable=False),
        sa.Column('semantic_hash', sa.String(length=64), nullable=False),
        sa.Column('entity_json', sa.JSON(), nullable=True),
        sa.Column('normalized_keywords', sa.JSON(), nullable=True),
        sa.Column('keyword_score', sa.Float(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_url'),
    )
    op.create_index('ix_ra_canonical_url', 'raw_articles', ['canonical_url'], unique=True)
    op.create_index('ix_ra_published_at', 'raw_articles', ['published_at'], unique=False)
    op.create_index('ix_ra_semantic_hash', 'raw_articles', ['semantic_hash'], unique=False)
    op.create_index('ix_ra_title_hash', 'raw_articles', ['title_hash'], unique=False)

    # 2. event_updates
    op.create_table('event_updates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('issue_id', sa.String(length=36), nullable=True),
        sa.Column('article_id', sa.String(length=36), nullable=False),
        sa.Column('update_type', sa.Enum('NEW', 'MINOR_UPDATE', 'MAJOR_UPDATE', 'DUP', name='updatetype'), nullable=False),
        sa.Column('update_score', sa.Float(), nullable=False),
        sa.Column('major_reasons', sa.JSON(), nullable=True),
        sa.Column('diff_summary', sa.Text(), nullable=True),
        sa.Column('duplicate_of_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['raw_articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_eu_issue_created', 'event_updates', ['issue_id', 'created_at'], unique=False)
    op.create_index('ix_event_updates_article_id', 'event_updates', ['article_id'], unique=False)
    op.create_index('ix_event_updates_issue_id', 'event_updates', ['issue_id'], unique=False)

    # 3. issue_keyword_states
    op.create_table('issue_keyword_states',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('issue_id', sa.String(length=36), nullable=False),
        sa.Column('normalized_keyword', sa.String(length=200), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'COOLDOWN', 'CLOSED', name='keywordlinkstatus'), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_iks_keyword_status_seen', 'issue_keyword_states', ['normalized_keyword', 'status', 'last_seen_at'], unique=False)
    op.create_index('ix_issue_keyword_states_issue_id', 'issue_keyword_states', ['issue_id'], unique=False)

    # 4. live_feed_items
    op.create_table('live_feed_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('issue_id', sa.String(length=36), nullable=True),
        sa.Column('update_id', sa.String(length=36), nullable=False),
        sa.Column('feed_type', sa.Enum('BREAKING', 'MAJOR', 'ALL', name='feedtype'), nullable=False),
        sa.Column('rank_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['update_id'], ['event_updates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lfi_feed_rank_created', 'live_feed_items', ['feed_type', 'rank_score', 'created_at'], unique=False)
    op.create_index('ix_live_feed_items_issue_id', 'live_feed_items', ['issue_id'], unique=False)
    op.create_index('ix_live_feed_items_update_id', 'live_feed_items', ['update_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_live_feed_items_update_id', table_name='live_feed_items')
    op.drop_index('ix_live_feed_items_issue_id', table_name='live_feed_items')
    op.drop_index('ix_lfi_feed_rank_created', table_name='live_feed_items')
    op.drop_table('live_feed_items')

    op.drop_index('ix_issue_keyword_states_issue_id', table_name='issue_keyword_states')
    op.drop_index('ix_iks_keyword_status_seen', table_name='issue_keyword_states')
    op.drop_table('issue_keyword_states')

    op.drop_index('ix_event_updates_issue_id', table_name='event_updates')
    op.drop_index('ix_event_updates_article_id', table_name='event_updates')
    op.drop_index('ix_eu_issue_created', table_name='event_updates')
    op.drop_table('event_updates')

    op.drop_index('ix_ra_title_hash', table_name='raw_articles')
    op.drop_index('ix_ra_semantic_hash', table_name='raw_articles')
    op.drop_index('ix_ra_published_at', table_name='raw_articles')
    op.drop_index('ix_ra_canonical_url', table_name='raw_articles')
    op.drop_table('raw_articles')

    # Enum 타입 정리
    sa.Enum(name='feedtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='keywordlinkstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='updatetype').drop(op.get_bind(), checkfirst=True)
