# Scheduler (APScheduler 워커)

`trend-korea-worker` 엔트리포인트로 실행되는 백그라운드 스케줄러.
APScheduler `BlockingScheduler`를 사용하며, 모든 잡은 `job_runs` 테이블에 실행 기록을 남긴다.

## 실행 방법

```bash
# 로컬 개발
uv run trend-korea-worker

# Docker (docker-entrypoint.sh에서 자동 실행)
# API 서버와 동일 컨테이너에서 백그라운드로 실행됨
```

## 잡 목록

| 잡 ID | 주기 | 트리거 | 설명 | 핸들러 |
|--------|------|--------|------|--------|
| `news_collect` | 15분 | interval | 뉴스 수집 + 분류 + 요약 전체 사이클 | `pipeline_jobs.run_news_collect_cycle` |
| `keyword_state_cleanup` | 1시간 | interval | 이슈 키워드 상태 전환 (ACTIVE→COOLDOWN→CLOSED) | `pipeline_jobs.cleanup_keyword_states` |
| `issue_status_reconcile` | 30분 | cron | 이슈 상태 조정 (ONGOING→CLOSED→REIGNITED) | `issue_jobs.reconcile_issue_status` |
| `search_rankings` | 매시 정각 | cron | 검색 랭킹 재계산 (최근 24시간 키워드 빈도) | `search_jobs.recalculate_search_rankings` |
| `community_hot_score` | 10분 | cron | 커뮤니티 게시글 댓글 수 동기화 | `community_jobs.recalculate_community_hot_score` |
| `cleanup_refresh_tokens` | 매일 03:00 | cron | 만료/폐기된 리프레시 토큰 정리 | `auth_jobs.cleanup_refresh_tokens` |

## 아키텍처

```
src/
├── worker_main.py              # 스케줄러 진입점 + 잡 등록
└── scheduler/
    ├── __init__.py
    ├── runner.py               # run_job() — 잡 실행 + job_runs 기록
    └── jobs/
        ├── __init__.py         # 배럴 import
        ├── pipeline_jobs.py    # 뉴스 수집/분류, 키워드 상태 정리
        ├── issue_jobs.py       # 이슈 상태 조정
        ├── search_jobs.py      # 검색 랭킹
        ├── community_jobs.py   # 커뮤니티 점수
        └── auth_jobs.py        # 토큰 정리
```

## 잡 실행 흐름

```
1. APScheduler가 트리거 시점에 람다 호출
2. runner.run_job(job_name, handler) 실행
   ├── SessionLocal()로 DB 세션 생성
   ├── handler(db) 호출
   ├── db.commit()
   └── job_runs 테이블에 실행 결과 기록
3. 실패 시 status="failed", detail에 에러 메시지 저장
```

### 잡 핸들러 시그니처

```python
def handler(db: Session) -> str | None:
    """잡 핸들러.

    Args:
        db: SQLAlchemy 세션 (runner가 commit/close 관리)

    Returns:
        실행 결과 요약 문자열 (job_runs.detail에 저장)
    """
```

## 뉴스 수집 파이프라인 잡 상세

### `news_collect` (15분 간격)

전체 파이프라인 1사이클을 실행한다:

```
키워드 수집 → 뉴스 크롤링 → 네이버 뉴스 → 기사 분류/중복 제거 → LLM 요약 → 피드 저장
```

**특이사항:**
- 파이프라인 내부에서 별도 DB 세션을 사용 (분류/피드 저장 시)
- `max_instances=1` + `coalesce=True`로 이전 사이클이 끝나지 않으면 건너뜀
- 네이버 뉴스 API는 `NAVER_API_CLIENT` 환경변수가 설정된 경우에만 활성화
- 결과 JSON은 `cycle_outputs/scheduled_<timestamp>/` 디렉토리에 저장
- 실행 기록: `job_runs` 테이블에 수집 건수, 분류 결과, 소요 시간 포함

**분류 결과 예시 (detail 컬럼):**
```
status=ok, articles=22, summaries=2, new=19, minor=0, major=0, dup=3, elapsed=32.5s
```

### `keyword_state_cleanup` (1시간 간격)

이슈 키워드의 생명주기를 자동 관리한다:

| 현재 상태 | 조건 | 전환 상태 |
|-----------|------|-----------|
| ACTIVE | `last_seen_at` 48시간 경과 | COOLDOWN |
| COOLDOWN | `last_seen_at` 120시간(48+72) 경과 | CLOSED |

- CLOSED 키워드는 이슈 매칭 후보에서 제외됨
- 새 기사가 유입되면 `_update_keyword_states()`에서 `last_seen_at` 갱신 → 재활성화

## 환경변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `SCHEDULER_TIMEZONE` | `Asia/Seoul` | 스케줄러 타임존 |
| `SCHEDULE_NEWS_COLLECT_MINUTES` | `15` | 뉴스 수집 사이클 간격 (분) |
| `SCHEDULE_KEYWORD_CLEANUP_MINUTES` | `60` | 키워드 상태 정리 간격 (분) |
| `NAVER_API_CLIENT` | (빈 문자열) | 설정 시 네이버 뉴스 API 활성화 |
| `NAVER_API_CLIENT_SECRET` | (빈 문자열) | 네이버 API 시크릿 |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | LLM 요약 API 엔드포인트 |
| `OLLAMA_DEFAULT_MODEL` | `gemma3:4b` | 요약에 사용할 모델 |

## CloudType 배포

CloudType에서는 `docker-entrypoint.sh`가 API 서버와 워커를 하나의 컨테이너에서 동시 실행한다:

```bash
# docker-entrypoint.sh 발췌
uvicorn src.main:app --host 0.0.0.0 --port 8000 &   # API (백그라운드)
trend-korea-worker &                                   # 워커 (백그라운드)
wait -n                                                # 둘 중 하나 종료 시 전체 종료
```

**주의사항:**
- 워커는 단일 인스턴스만 실행해야 한다 (중복 실행 시 잡이 이중 실행됨)
- CloudType의 인스턴스 수(replicas)를 2 이상으로 설정하면 워커도 복제되므로, 워커를 별도 서비스로 분리하거나 리더 선출이 필요함
- `RUN_MIGRATIONS=true` 환경변수 설정 시 컨테이너 시작 시 Alembic 마이그레이션 자동 실행

## 실행 기록 확인

```sql
-- 최근 잡 실행 기록
SELECT job_name, status, detail, started_at, finished_at
FROM job_runs
ORDER BY started_at DESC
LIMIT 20;

-- 뉴스 수집 잡 성공률
SELECT
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (finished_at - started_at))) as avg_seconds
FROM job_runs
WHERE job_name = 'news_collect'
  AND started_at >= NOW() - INTERVAL '24 hours'
GROUP BY status;
```

## 새 잡 추가 방법

1. `src/scheduler/jobs/` 아래에 잡 파일 생성
2. 핸들러 함수 작성 (`(db: Session) -> str | None` 시그니처)
3. `src/scheduler/jobs/__init__.py`에 배럴 import 추가
4. `src/worker_main.py`의 `build_scheduler()`에 `scheduler.add_job()` 등록
5. 간격을 환경변수로 제어하려면 `src/core/config.py`의 `Settings`에 설정 추가
