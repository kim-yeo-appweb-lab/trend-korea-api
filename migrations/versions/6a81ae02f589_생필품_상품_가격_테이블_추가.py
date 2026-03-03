"""생필품 상품·가격 테이블 추가

Revision ID: 6a81ae02f589
Revises: a27b8d1a6e1a
Create Date: 2026-02-24 09:09:31.080685
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a81ae02f589'
down_revision = 'a27b8d1a6e1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('product_info',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('good_id', sa.String(length=20), nullable=False),
    sa.Column('good_name', sa.String(length=70), nullable=False),
    sa.Column('good_unit_div_code', sa.String(length=10), nullable=True),
    sa.Column('good_base_cnt', sa.String(length=10), nullable=True),
    sa.Column('good_smlcls_code', sa.String(length=20), nullable=True),
    sa.Column('detail_mean', sa.String(length=200), nullable=True),
    sa.Column('good_total_cnt', sa.String(length=15), nullable=True),
    sa.Column('good_total_div_code', sa.String(length=10), nullable=True),
    sa.Column('product_entp_code', sa.String(length=70), nullable=True),
    sa.Column('raw_data', sa.Text(), nullable=True),
    sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pi_fetched_at', 'product_info', ['fetched_at'], unique=False)
    op.create_index(op.f('ix_product_info_good_id'), 'product_info', ['good_id'], unique=True)
    op.create_table('product_prices',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('good_id', sa.String(length=20), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('store_name', sa.String(length=100), nullable=True),
    sa.Column('on_sale', sa.Boolean(), nullable=False),
    sa.Column('survey_date', sa.String(length=10), nullable=True),
    sa.Column('raw_data', sa.Text(), nullable=True),
    sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['good_id'], ['product_info.good_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pp_fetched_at', 'product_prices', ['fetched_at'], unique=False)
    op.create_index('ix_pp_survey_date', 'product_prices', ['survey_date'], unique=False)
    op.create_index(op.f('ix_product_prices_good_id'), 'product_prices', ['good_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_prices_good_id'), table_name='product_prices')
    op.drop_index('ix_pp_survey_date', table_name='product_prices')
    op.drop_index('ix_pp_fetched_at', table_name='product_prices')
    op.drop_table('product_prices')
    op.drop_index(op.f('ix_product_info_good_id'), table_name='product_info')
    op.drop_index('ix_pi_fetched_at', table_name='product_info')
    op.drop_table('product_info')
