"""네이버 뉴스 기사 테이블 추가

Revision ID: c5e056319c71
Revises: 6a81ae02f589
Create Date: 2026-02-24 10:04:11.420119
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5e056319c71'
down_revision = '6a81ae02f589'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('naver_news_articles',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('keyword', sa.String(length=100), nullable=False),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('original_link', sa.String(length=1000), nullable=False),
    sa.Column('naver_link', sa.String(length=1000), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('pub_date', sa.String(length=40), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('raw_data', sa.Text(), nullable=True),
    sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_naver_news_articles_keyword'), 'naver_news_articles', ['keyword'], unique=False)
    op.create_index('ix_nna_fetched_at', 'naver_news_articles', ['fetched_at'], unique=False)
    op.create_index('ix_nna_keyword_pub', 'naver_news_articles', ['keyword', 'pub_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_nna_keyword_pub', table_name='naver_news_articles')
    op.drop_index('ix_nna_fetched_at', table_name='naver_news_articles')
    op.drop_index(op.f('ix_naver_news_articles_keyword'), table_name='naver_news_articles')
    op.drop_table('naver_news_articles')
