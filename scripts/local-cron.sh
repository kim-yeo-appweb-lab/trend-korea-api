#!/usr/bin/env bash
# 로컬 crontab용 래퍼 스크립트
# cron은 최소 환경에서 실행되므로, 프로젝트 루트로 이동 + PATH 설정이 필수.
#
# 사용법:
#   ./scripts/local-cron.sh <job_name>
#   ./scripts/local-cron.sh news_collect

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
JOB_NAME="${1:?사용법: $0 <job_name>}"
LOG_FILE="${LOG_DIR}/cron_${JOB_NAME}.log"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# Homebrew + uv PATH (macOS)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cd "$PROJECT_DIR"

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] ${JOB_NAME} 시작 ===" >> "$LOG_FILE"
uv run trend-korea-cron "$JOB_NAME" >> "$LOG_FILE" 2>&1
echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] ${JOB_NAME} 완료 ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
