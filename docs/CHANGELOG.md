# Changelog

프로젝트 커밋 히스토리와 현재 진행 중인 작업을 정리한 문서.

---

## 커밋된 변경 사항 (main 브랜치)

### Phase 0 — 프로젝트 초기 셋업

| 커밋 | 설명 |
|------|------|
| `081a7c4` | 프로젝트 루트 생성 (Initial commit) |
| `15a0a5a` | `.env.example` 플레이스홀더 정리 |
| `2ab25ae` | 프로젝트 이름 → `trend-korea-api` |
| `c7170fd` | 문서를 `docs/`로 이동, 배포 가이드 추가 |
| `d367448` | Docker 배포 환경 구성 |

### Phase 1 — 코어 API 및 커뮤니티

| 커밋 | 설명 |
|------|------|
| `b70c74f` | events: 생성 시 tag/source ID 유효성 검증 |
| `030cf3b` | issues: 생성 시 tag/source ID 유효성 검증 |
| `6cb6b1c` | Swagger responses 및 스텁 문서 보완 |
| `a386906` | deprecated `datetime.utcnow()` → `datetime.now(timezone.utc)` 교체 |
| `4ad0054` | README에 테스트 섹션 추가 |

### Phase 2 — 아키텍처 리팩터링

| 커밋 | 설명 |
|------|------|
| `f099e0a` | 도메인 기반 → **레이어 기반** 폴더 구조 전환 |
| `3d45e45` | README/CLAUDE.md 전면 갱신 |
| `1faee47` | 파이프라인 모듈을 `src/utils/` 폴더 단위로 재구조화 |
| `45d11ce` | 파이프라인 모듈 구조 문서화 |

### Phase 3 — 커뮤니티 버그 픽스

| 커밋 | 설명 |
|------|------|
| `922265b` | 존재하지 않는 tagIds 사전 검증 추가 (PR #2) |
| `c2d4bbf` | Swagger에 태그 검증 404 응답 문서 추가 (PR #3) |
| `9e579f6` | `authorNickname`/`authorImage` null 반환 버그 수정 (PR #5) |

### Phase 4 — 뉴스 수집 파이프라인 구축

| 커밋 | 설명 |
|------|------|
| `974b0c8` | `.gitignore`에 파이프라인 출력 파일 제외 |
| `ab0821a` | DB, schedule 정리 |
| `b487ab9` | 뉴스 분류 시스템 신규 테이블 및 Enum 추가 (`raw_articles`, `issue_keyword_states`, `event_updates`, `live_feed_items`) |
| `4d72098` | 뉴스 업데이트 자동 분류 시스템 구현 (URL exact + hash near-dup 중복 제거, 이슈 키워드 자동 매칭, NEW/MINOR/MAJOR/DUP 4단계 분류) |
| `83ed569` | 라이브 피드 `GET /feed/live` 및 이슈 타임라인 `GET /issues/{id}/timeline` API 추가 |
| `9e26ca8` | 뉴스 수집 파이프라인 스케줄러 잡 등록 (`news_collect` 15분, `keyword_state_cleanup` 1시간) |
| `930b4db` | 7개 테이블 VARCHAR(20) → PostgreSQL 네이티브 ENUM 변환 |
| `04fdff9` | 뉴스 분류 시스템 테스트 41개 케이스 추가 |

### Phase 5 — 문서화 및 규칙 정비

| 커밋 | 설명 |
|------|------|
| `807d496` | 스케줄러 README 추가 |
| `7394c4d` | code-documenter 스킬 마크다운 테이블 정렬 |
| `aa68605` | `.gitignore`에 `.omc/` 추가 |
| `2b5d983` | `agent_docs/` → `.claude/rules/`로 이전 |
| `7c3f23b` | Claude 규칙 추가 (브랜칭 전략, 커밋 규칙) |
| `5e3fe6f` | 어드민 분리 반영 — PRD/ROADMAP 작성 |

---

## 현재 진행 중 (미커밋 변경 사항)

아래 항목은 작업 브랜치 또는 로컬에서 진행 중이며 아직 커밋되지 않은 상태.

### 1. 모델 대규모 재구성 — `db/` → `models/` 통합

**변경 파일**: 45개 (신규 15개, 수정 19개, 삭제 11개)
**요약**: `+1,432줄 / -777줄`

기존에 `src/db/` 디렉토리에 흩어져 있던 단일 모델 파일들을 도메인별 `src/models/` 파일로 통합.

| 삭제된 파일 (src/db/) | 이동 대상 (src/models/) |
|------------------------|--------------------------|
| `crawled_keyword.py` | `pipeline.py` |
| `event_update.py` | `feed.py` |
| `issue_keyword_state.py` | `issues.py` |
| `job.py` | `scheduler.py` |
| `keyword_intersection.py` | `pipeline.py` |
| `live_feed_item.py` | `feed.py` |
| `naver_news.py` | `pipeline.py` |
| `news_channel.py` | `sources.py` |
| `news_summary.py` | `news_summary.py` |
| `product.py` | `pipeline.py` |
| `raw_article.py` | `pipeline.py` |

`db/__init__.py` 배럴 import를 새 경로로 갱신 완료.

### 2. 신규 도메인 추가

#### 알림 시스템 (Notification)
- **모델**: `Notification`, `UserAlertRule` (`src/models/notification.py`)
- **스키마**: `src/schemas/notification.py`
- **CRUD**: `src/crud/notification.py`
- **SQL**: `src/sql/notification.py`
- **API**: `src/api/v1/users.py`에 `/users/me/alert-rules` CRUD, `/users/me/notifications` 조회/읽음 처리 엔드포인트 추가
- **Enum**: `NotificationType` (major_update, trigger_update, comment_reply, keyword_match, system)

#### 구독 시스템 (Subscription)
- **모델**: `KeywordSubscription`, `KeywordMatch` (`src/models/subscription.py`)
- **스키마**: `src/schemas/subscription.py`
- **CRUD**: `src/crud/subscription.py`
- **SQL**: `src/sql/subscription.py`
- **API**: `src/api/v1/users.py`에 `/users/me/subscriptions` CRUD 엔드포인트 추가

### 3. 이슈 모델 확장

`src/models/issues.py`에 3개 모델 추가:

| 모델 | 용도 |
|------|------|
| `IssueKeywordState` | 이슈-키워드 연결 상태 (자동 매칭용) |
| `IssueKeywordAlias` | 키워드 별칭 (정규화 매핑) |
| `IssueRankSnapshot` | 이슈 랭킹 스냅샷 (시계열 추적) |

### 4. 파이프라인 아키텍처 개선

#### 헤드라인 기반 수집으로 전환
- `src/utils/keyword_crawler/headline_extractor.py`: 메인페이지 헤드라인 URL 추출 (+146줄)
- `src/utils/news_collector/content_fetcher.py`: 신규 — 본문 수집 모듈
- `src/utils/pipeline/orchestrator.py`: 키워드→헤드라인→ES 매칭→본문 수집→분류→요약 6단계 파이프라인으로 확장 (+289줄)
- `src/utils/pipeline/quality_gate.py`: 신규 — 중복 비율 품질 게이트

#### Elasticsearch 통합
- `src/utils/elasticsearch/client.py`: ES 클라이언트 래퍼
- `src/utils/elasticsearch/indexer.py`: 기사 인덱서
- `src/utils/elasticsearch/searcher.py`: nori 형태소 분석 기반 검색

#### 뉴스 요약기 개선
- `src/utils/news_summarizer/summarizer.py`: 리팩터링 (+56줄)
- `src/utils/news_summarizer/prompt_builder.py`: 프롬프트 개선 (+33줄)

### 5. 스케줄러 → supercronic 전환

APScheduler 인프로세스 방식에서 **supercronic** 기반 cron 실행으로 전환:

- `Dockerfile`: supercronic 바이너리 설치
- `docker-entrypoint.sh`: supercronic 백그라운드 + uvicorn 포그라운드 구조
- `crontab`: 8개 잡 정의 (10분 간격 통일)
- `src/scheduler/cli.py`: 신규 — `trend-korea-cron` CLI 진입점
- `docker-compose.yml`: Elasticsearch 서비스 추가

### 6. 피드 API 강화

- `src/api/v1/feed.py`: 신규 엔드포인트 추가 (+27줄)
- `src/crud/feed.py`: 피드 비즈니스 로직 확장 (+89줄)
- `src/sql/feed.py`: 피드 데이터 액세스 쿼리 추가 (+63줄)
- `src/schemas/feed.py`: 피드 스키마 확장 (+16줄)

### 7. Alembic 마이그레이션

- `5365fe70a19c`: Phase A-F metrics 컬럼, 랭킹, 별칭, 알림, 구독, 캘린더 테이블 마이그레이션

### 8. 기타

- `pyproject.toml`: 의존성 추가
- `tests/conftest.py`: 테스트 픽스처 업데이트
- `scripts/local-cron.sh`: 로컬 개발용 cron 스크립트
- 각 유틸리티 모듈에 README.md 추가

---

## 아키텍처 변화 요약

```
Before (Phase 4까지):
  keyword_crawler → naver_news_crawler → news_summarizer
                                          ↓
                    update_classifier → feed_builder

After (현재 진행 중):
  keyword_crawler + headline_extractor
          ↓
  Elasticsearch nori 매칭
          ↓
  news_collector (본문 수집)
          ↓
  update_classifier → news_summarizer → feed_builder → quality_gate
```

스케줄러도 APScheduler → supercronic으로 전환하여 각 잡이 독립 프로세스로 실행됨.
