"""키워드 교집합 테이블 추가

Revision ID: 24b659aec956
Revises: c5e056319c71
Create Date: 2026-02-24 14:37:45.706556
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24b659aec956'
down_revision = 'c5e056319c71'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('keyword_intersections',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('keyword', sa.String(length=100), nullable=False),
    sa.Column('channel_count', sa.Integer(), nullable=False),
    sa.Column('total_count', sa.Integer(), nullable=False),
    sa.Column('channel_codes', sa.Text(), nullable=False),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('min_channels', sa.Integer(), nullable=False),
    sa.Column('crawled_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keyword_intersections_channel_count'), 'keyword_intersections', ['channel_count'], unique=False)
    op.create_index(op.f('ix_keyword_intersections_crawled_at'), 'keyword_intersections', ['crawled_at'], unique=False)
    op.create_index(op.f('ix_keyword_intersections_keyword'), 'keyword_intersections', ['keyword'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_keyword_intersections_keyword'), table_name='keyword_intersections')
    op.drop_index(op.f('ix_keyword_intersections_crawled_at'), table_name='keyword_intersections')
    op.drop_index(op.f('ix_keyword_intersections_channel_count'), table_name='keyword_intersections')
    op.drop_table('keyword_intersections')
