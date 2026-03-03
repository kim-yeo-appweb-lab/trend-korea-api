"""chore(db): VARCHAR 컬럼을 네이티브 ENUM 타입으로 변환

기존 마이그레이션이 VARCHAR(20)으로 생성한 Enum 컬럼들을
PostgreSQL 네이티브 ENUM 타입으로 변환한다.
PG ENUM 타입은 create_all()에 의해 이미 생성되어 있다.

변환 대상:
- events.importance → importance
- events.verification_status → verificationstatus
- issues.status → issuestatus
- users.role → userrole
- triggers.type → triggertype
- sources.entity_type → sourceentitytype
- tags.type → tagtype

Revision ID: 6f92b865ce85
Revises: c1ffbc23a48a
Create Date: 2026-03-03 17:17:14.345736
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '6f92b865ce85'
down_revision = 'c1ffbc23a48a'
branch_labels = None
depends_on = None

# (table, column, enum_type_name)
_CONVERSIONS = [
    ("events", "importance", "importance"),
    ("events", "verification_status", "verificationstatus"),
    ("issues", "status", "issuestatus"),
    ("users", "role", "userrole"),
    ("triggers", "type", "triggertype"),
    ("sources", "entity_type", "sourceentitytype"),
    ("tags", "type", "tagtype"),
]


def upgrade() -> None:
    for table, column, enum_type in _CONVERSIONS:
        op.execute(
            f'ALTER TABLE "{table}" '
            f'ALTER COLUMN "{column}" TYPE {enum_type} '
            f'USING "{column}"::{enum_type}'
        )


def downgrade() -> None:
    for table, column, enum_type in reversed(_CONVERSIONS):
        op.execute(
            f'ALTER TABLE "{table}" '
            f'ALTER COLUMN "{column}" TYPE VARCHAR(20) '
            f'USING "{column}"::text'
        )
