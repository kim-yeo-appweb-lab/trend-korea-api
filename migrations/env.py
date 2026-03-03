from __future__ import with_statement

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.core.config import get_settings
from src.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

target_metadata = Base.metadata


def _compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    """JSONB↔JSON 등 PostgreSQL 표면적 타입 차이를 무시한다."""
    from sqlalchemy import JSON
    from sqlalchemy.dialects.postgresql import JSONB

    # JSONB ↔ JSON: 모델은 JSON(SQLite 호환), DB는 JSONB — 무시
    if isinstance(inspected_type, JSONB) and isinstance(metadata_type, JSON):
        return False
    if isinstance(inspected_type, JSON) and isinstance(metadata_type, JSONB):
        return False

    # 기본 비교 로직 사용
    return None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=_compare_type,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=_compare_type,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
