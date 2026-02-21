# Alembic 마이그레이션

## 마이그레이션 생성

```bash
# 모델 변경사항을 자동 감지하여 마이그레이션 파일 생성
alembic revision --autogenerate -m "add users table"

# 수동 마이그레이션 (빈 파일 생성)
alembic revision -m "add custom index"
```

## 마이그레이션 적용

```bash
# 최신 버전으로 업그레이드
alembic upgrade head

# 한 단계만 업그레이드
alembic upgrade +1

# 특정 리비전으로 업그레이드
alembic upgrade <revision_id>
```

## 롤백

```bash
# 한 단계 롤백
alembic downgrade -1

# 특정 리비전으로 롤백
alembic downgrade <revision_id>

# 모든 마이그레이션 롤백 (초기 상태)
alembic downgrade base
```

## 상태 확인

```bash
# 현재 리비전 확인
alembic current

# 마이그레이션 히스토리 조회
alembic history --verbose

# 적용되지 않은 마이그레이션 확인
alembic heads
```

## env.py 패턴

```python
from trend_korea.core.config import get_settings
from trend_korea.core.session import engine
from trend_korea.models.base import Base

# autogenerate가 모델 변경사항을 감지하도록 metadata 설정
target_metadata = Base.metadata

def run_migrations_online() -> None:
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()
```

## 마이그레이션 파일 구조

```python
"""add users table

Revision ID: a1b2c3d4e5f6
Revises: 9z8y7x6w5v4u
Create Date: 2024-01-15 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "9z8y7x6w5v4u"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
```

## Quick Reference

| 명령어 | 설명 |
|--------|------|
| `alembic revision --autogenerate -m "메시지"` | 자동 마이그레이션 생성 |
| `alembic revision -m "메시지"` | 수동 마이그레이션 생성 |
| `alembic upgrade head` | 최신으로 업그레이드 |
| `alembic upgrade +1` | 한 단계 업그레이드 |
| `alembic downgrade -1` | 한 단계 롤백 |
| `alembic downgrade base` | 전체 롤백 |
| `alembic current` | 현재 리비전 확인 |
| `alembic history` | 히스토리 조회 |
| `alembic heads` | 최신 리비전 확인 |
| `target_metadata = Base.metadata` | env.py 핵심 설정 |
