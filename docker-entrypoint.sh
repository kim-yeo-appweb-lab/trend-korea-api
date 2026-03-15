#!/usr/bin/env bash
set -euo pipefail

# 조건부 Alembic 마이그레이션
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "[entrypoint] Alembic 마이그레이션 실행..."
    if ! alembic upgrade head; then
        echo "[entrypoint] upgrade 실패 — 기존 테이블 감지, stamp head 실행..."
        alembic stamp head
    fi
fi

# supercronic (cron 스케줄러, 백그라운드)
supercronic /app/crontab &
CRON_PID=$!

# API 서버 (포그라운드, PID 1)
exec uvicorn trend_korea.main:app \
    --host "${APP_HOST:-0.0.0.0}" \
    --port "${APP_PORT:-8000}" \
    --no-access-log
