# 스케줄러 잡 데이터 적재 맵

각 스케줄러 잡이 어떤 DB 테이블에 데이터를 적재/수정/삭제하는지 정리한 문서.

## 잡 실행 방법

```bash
# 프로덕션 (DB 저장 + JobRun 기록)
trend-korea-cron <job_name>

# 테스트 (DB 저장 없이 JSON 출력, news_collect 전용)
trend-korea-cron news_collect --top-n 10 --max-keywords 3 --limit 2
```

---

## 공통: run_job 래퍼

모든 잡은 `run_job()` 래퍼를 통해 실행되며, 성공/실패와 무관하게 아래 테이블에 기록됩니다.

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `job_runs` | `JobRun` | INSERT | 잡 이름, 상태(success/failed), 상세 메시지, 시작/종료 시간, metrics |

---

## 잡별 데이터 흐름

### 1. keyword_collect (트렌드 키워드 수집)

**주기:** 10분 | **핸들러:** `pipeline_jobs.collect_keywords`

뉴스 채널 10개의 메인 페이지에서 키워드를 추출하여 DB에 저장.

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `crawled_keywords` | `CrawledKeyword` | INSERT | 채널별 + 통합 키워드 (빈도, 순위, 채널 정보) |
| `keyword_intersections` | `KeywordIntersection` | INSERT | 3개 이상 채널에서 동시 등장한 교집합 키워드 |

---

### 2. news_collect (뉴스 수집 파이프라인)

**주기:** 10분 | **핸들러:** `pipeline_jobs.run_news_collect_cycle`

키워드 수집 → 뉴스 크롤링 → 분류/중복 제거 → 요약 전체 파이프라인 실행.
각 단계의 결과가 해당 테이블에 독립적으로 저장된다.

#### 단계 1: 키워드 수집

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `crawled_keywords` | `CrawledKeyword` | INSERT | 채널별 + 통합 키워드 (빈도, 순위, 채널 정보) |
| `keyword_intersections` | `KeywordIntersection` | INSERT | 교집합 키워드 (3+ 채널) |

#### 단계 2: 뉴스 크롤링

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `naver_news_articles` | `NaverNewsArticle` | INSERT | 네이버 뉴스 검색 API 원본 결과 |

#### 단계 3: 기사 분류/중복 제거

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `raw_articles` | `RawArticle` | INSERT | 정규화된 뉴스 기사 (URL, 제목, 본문, 소스) |
| `event_updates` | `EventUpdate` | INSERT | 분류 결과 (NEW/MINOR/MAJOR/DUP), 매칭된 이슈 |
| `live_feed_items` | `LiveFeedItem` | INSERT | 피드 항목 (ALL/BREAKING/MAJOR 타입) |
| `issue_keyword_states` | `IssueKeywordState` | UPDATE | 이슈-키워드 매칭 시 `last_seen_at` 갱신 |
| `notifications` | `Notification` | INSERT | MAJOR_UPDATE 시 이슈 추적자에게 알림 생성 |
| `keyword_matches` | `KeywordMatch` | INSERT | 키워드 구독과 매칭된 기사 기록 |

#### 단계 4: 뉴스 요약

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `news_summary_batches` | `NewsSummaryBatch` | INSERT | 요약 배치 메타데이터 (모델, 토큰 사용량) |
| `news_keyword_summaries` | `NewsKeywordSummary` | INSERT | 키워드별 요약 결과 (요약문, 감성, 카테고리) |
| `news_summary_tags` | `NewsSummaryTag` | INSERT | 요약에서 추출된 태그 |

---

### 3. keyword_state_cleanup (키워드 상태 정리)

**주기:** 10분 | **핸들러:** `pipeline_jobs.cleanup_keyword_states`

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `issue_keyword_states` | `IssueKeywordState` | UPDATE | ACTIVE → COOLDOWN (48시간 경과) |
| `issue_keyword_states` | `IssueKeywordState` | UPDATE | COOLDOWN → CLOSED (120시간 경과) |

---

### 4. issue_status_reconcile (이슈 상태 조정)

**주기:** 10분 | **핸들러:** `issue_jobs.reconcile_issue_status`

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `issues` | `Issue` | UPDATE | ONGOING → CLOSED (30일 비활동) |
| `issues` | `Issue` | UPDATE | CLOSED → REIGNITED (7일 내 재발) |

---

### 5. issue_rankings (이슈 랭킹 스냅샷)

**주기:** 10분 | **핸들러:** `feed_jobs.calculate_issue_rankings`

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `issue_rank_snapshots` | `IssueRankSnapshot` | INSERT | 상위 20개 이슈 랭킹 (점수, 업데이트 수, 추적자 수) |
| `issue_rank_snapshots` | `IssueRankSnapshot` | DELETE | 7일 이전 스냅샷 삭제 |

---

### 6. search_rankings (검색 랭킹 재계산)

**주기:** 10분 | **핸들러:** `search_jobs.recalculate_search_rankings`

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `search_rankings` | `SearchRanking` | DELETE | 7일 이전 랭킹 삭제 |
| `search_rankings` | `SearchRanking` | INSERT | 최근 24시간 이벤트/이슈/게시글 제목에서 상위 10개 키워드 |

---

### 7. community_hot_score (인기 게시글 점수)

**주기:** 10분 | **핸들러:** `community_jobs.recalculate_community_hot_score`

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `posts` | `Post` | UPDATE | `comment_count` 필드 갱신 |

---

### 8. cleanup_refresh_tokens (만료 토큰 정리)

**주기:** 10분 | **핸들러:** `auth_jobs.cleanup_refresh_tokens`

| 테이블 | 모델 | 작업 | 설명 |
|--------|------|------|------|
| `refresh_tokens` | `RefreshToken` | DELETE | 만료되었거나 30일 이전 취소된 토큰 삭제 |

---

## 데이터 보존 정책

| 테이블 | 보존 기간 | 정리 주체 |
|--------|-----------|-----------|
| `issue_rank_snapshots` | 7일 | `issue_rankings` 잡 |
| `search_rankings` | 7일 | `search_rankings` 잡 |
| `refresh_tokens` | 만료 즉시 / 취소 후 30일 | `cleanup_refresh_tokens` 잡 |
| `crawled_keywords` | 무기한 | - |
| `raw_articles` | 무기한 | - |
| `job_runs` | 무기한 | - |

---

## 테이블 → 잡 역참조

특정 테이블에 데이터를 적재하는 잡을 빠르게 찾기 위한 역참조 표.

| 테이블 | 적재하는 잡 |
|--------|------------|
| `crawled_keywords` | keyword_collect, news_collect |
| `keyword_intersections` | keyword_collect, news_collect |
| `naver_news_articles` | news_collect |
| `raw_articles` | news_collect |
| `event_updates` | news_collect |
| `live_feed_items` | news_collect |
| `notifications` | news_collect |
| `keyword_matches` | news_collect |
| `news_summary_batches` | news_collect |
| `news_keyword_summaries` | news_collect |
| `news_summary_tags` | news_collect |
| `issue_keyword_states` | news_collect (UPDATE), keyword_state_cleanup (UPDATE) |
| `issues` | issue_status_reconcile (UPDATE) |
| `issue_rank_snapshots` | issue_rankings |
| `search_rankings` | search_rankings |
| `posts` | community_hot_score (UPDATE) |
| `refresh_tokens` | cleanup_refresh_tokens (DELETE) |
| `job_runs` | 모든 잡 (공통) |
