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

# API 서버를 백그라운드로 시작
uvicorn trend_korea.main:app \
    --host "${APP_HOST:-0.0.0.0}" \
    --port "${APP_PORT:-8000}" \
    --no-access-log &
API_PID=$!

# 워커(스케줄러)를 포그라운드로 시작
trend-korea-worker &
WORKER_PID=$!

# 시그널 핸들러: 두 프로세스 모두 종료
trap 'kill $API_PID $WORKER_PID 2>/dev/null; wait' SIGTERM SIGINT

# 어느 하나라도 종료되면 전체 종료
wait -n
kill $API_PID $WORKER_PID 2>/dev/null
wait
