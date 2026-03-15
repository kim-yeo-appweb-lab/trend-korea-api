# 수집 서비스 AI 개발 가이드
작성일: 2026-03-03  
목적: AI 코딩 에이전트가 바로 구현 가능한 형태로 작업 단위를 표준화한다.

## 1. 구현 목표 (이번 스코프)
- 뉴스 수집 결과를 자동으로 `NEW / MINOR_UPDATE / MAJOR_UPDATE / DUP`로 분류한다.
- 동일 이슈키워드면 기존 이슈 타임라인에 자동 누적한다.
- 속보 피드(`live`)와 이슈 타임라인 API에서 업데이트를 노출한다.
- 사람 개입 없이 배치/워커로 반복 실행 가능해야 한다.

## 2. 소스 오브 트루스
- 기존 기획서: [수집 서비스 개발기획서.md](/Users/josephkim/Project/trend-korea-backend/docs/수집%20서비스%20개발기획서.md)
- 현재 파이프라인 코드:
  - [orchestrator.py](/Users/josephkim/Project/trend-korea-backend/src/utils/pipeline/orchestrator.py)
  - [crawler.py](/Users/josephkim/Project/trend-korea-backend/src/utils/keyword_crawler/crawler.py)
  - [fetcher.py](/Users/josephkim/Project/trend-korea-backend/src/utils/naver_news_crawler/fetcher.py)
  - [summarizer.py](/Users/josephkim/Project/trend-korea-backend/src/utils/news_summarizer/summarizer.py)

## 3. 작업 순서 (AI 실행용)
1. DB 스키마 추가
2. 분류 로직 모듈 추가
3. 오케스트레이터 단계 삽입
4. API 엔드포인트 추가
5. 테스트/검증 코드 추가
6. 메트릭/로그 추가

## 4. DB 스키마 (최소)
### 4.1 신규 테이블
- `raw_articles`
  - `id`, `canonical_url`, `title`, `content_text`, `published_at`, `source`, `entity_json`, `normalized_keywords`, `title_hash`, `semantic_hash`, `created_at`
- `issue_keyword_state`
  - `id`, `issue_id`, `normalized_keyword`, `status(active|cooldown|closed)`, `last_seen_at`, `created_at`, `updated_at`
- `event_updates`
  - `id`, `issue_id`, `article_id`, `update_type(NEW|MINOR_UPDATE|MAJOR_UPDATE|DUP)`, `update_score`, `major_reasons(jsonb)`, `diff_summary`, `created_at`
- `live_feed_items`
  - `id`, `issue_id`, `update_id`, `feed_type(breaking|major|all)`, `rank_score`, `created_at`

### 4.2 인덱스
- `raw_articles(canonical_url unique)`
- `raw_articles(published_at desc)`
- `issue_keyword_state(normalized_keyword, status, last_seen_at desc)`
- `event_updates(issue_id, created_at desc)`
- `live_feed_items(feed_type, rank_score desc, created_at desc)`

## 5. 핵심 판정 규칙
## 5.1 처리 순서
1. DUP 1차: canonical URL exact
2. DUP 2차: title/content hash near-duplicate
3. 후보 이슈 검색: 최근 72시간 active/cooldown
4. 후보 점수 계산: keyword/entity/semantic/time/source
5. 라벨 결정: `NEW` / `MINOR_UPDATE` / `MAJOR_UPDATE` / `DUP`

## 5.2 점수식
```text
update_score =
  0.35 * semantic_similarity +
  0.20 * entity_overlap +
  0.20 * time_proximity +
  0.15 * keyword_overlap +
  0.10 * source_weight -
  duplicate_penalty
```

## 5.3 임계값
- `score < 0.45` => `NEW`
- `0.45 <= score < 0.70` => `MINOR_UPDATE`
- `score >= 0.70` + major 조건 충족 => `MAJOR_UPDATE`
- DUP 필터에서 걸리면 무조건 `DUP`

## 5.4 MAJOR 조건
- 숫자 변화(인명/금액/규모 등)
- 상태 변화(검토->확정, 수사->기소 등)
- 핵심 주체 변화(새 기관/인물)

## 6. 코드 구조 제안
## 6.1 신규 모듈
- `src/utils/pipeline/update_classifier.py`
  - `normalize_keyword()`
  - `find_candidate_issues()`
  - `compute_update_score()`
  - `classify_update_type()`
  - `build_diff_summary()`

## 6.2 오케스트레이터 변경
- [orchestrator.py](/Users/josephkim/Project/trend-korea-backend/src/utils/pipeline/orchestrator.py)에 단계 추가
  - `collect -> normalize -> dedup -> match/classify -> summarize -> persist_feed`

## 6.3 의사코드
```python
for article in collected_articles:
    if is_duplicate(article):
        save_update(type="DUP")
        continue

    candidates = find_candidate_issues(article, hours=72, top_k=5)
    score, best_issue, reasons = score_candidates(article, candidates)
    label = classify(score, reasons)

    if label == "NEW":
        issue_id = create_issue(article)
    else:
        issue_id = best_issue.id

    diff = build_diff_summary(issue_id, article)
    update_id = append_update(issue_id, article, label, score, reasons, diff)
    push_live_feed(issue_id, update_id, label)
```

## 7. API 추가 스펙 (최소)
### 7.1 `GET /api/v1/feed/live`
- query: `cursor`, `limit`, `type(breaking|major|all)`
- response: `items[{issueId, updateType, diffSummary, rankScore, occurredAt}]`

### 7.2 `GET /api/v1/issues/{issue_id}/timeline`
- response: `items[{updateType, summary, diffSummary, sources, occurredAt}]`

## 8. 테스트 기준
## 8.1 단위 테스트
- DUP 판정 정확성
- update_score 계산 재현성
- 임계값 라벨 분류 케이스
- MAJOR 조건 감지 케이스

## 8.2 통합 테스트
- 입력 기사 세트 -> 기대 라벨/이슈 연결 결과 검증
- 동일 키워드 5건 연속 유입 시 타임라인 append 검증
- 10~20분 재전송 기사 억제 검증

## 9. 완료 조건 (Definition of Done)
- 신규 기사 자동 분류가 동작한다.
- 동일 이슈키워드 업데이트 누적이 동작한다.
- live feed/timeline API로 결과 조회 가능하다.
- 실패 시 재시도/로그가 남는다.
- KPI 로그(업데이트 연결율, DUP 억제율, MAJOR 정밀도) 수집이 가능하다.

## 10. 구현 시 주의사항
- 규칙 기반을 기본으로 하고, 모델/LLM은 보정 단계로만 사용한다.
- 기사 원문 재배포는 피하고 요약/링크 중심으로 저장한다.
- 멱등성 키를 반드시 적용해 중복 삽입을 방지한다.
- 임계값은 상수로 하드코딩하지 말고 설정값으로 분리한다.

---

## 11. 구현 완료 체크리스트 (2026-03-10 기준)

### 완료 항목 ✅
- [x] DB 스키마: `raw_articles`, `issue_keyword_states`, `event_updates`, `live_feed_items` 생성 + 마이그레이션 적용
- [x] 분류 로직: `update_classifier.py` — URL/해시 중복 제거, 이슈 키워드 매칭, 점수 계산, NEW/MINOR/MAJOR/DUP 분류
- [x] MAJOR 조건 감지: 수치 변화, 상태 변화(검토→확정 등), 핵심 주체 변화
- [x] diff_summary 자동 생성: `_build_diff_summary()` 구현
- [x] 속보 자동 판정: `score ≥ 0.85` → `FeedType.BREAKING` (feed_builder.py)
- [x] 피드 빌더: `feed_builder.py` — 분류 결과 → LiveFeedItem 변환 + DB 저장
- [x] 오케스트레이터 확장: 4단계 → 5단계 (분류 단계 삽입, DUP 제외 기사만 요약)
- [x] `--no-classify` CLI 플래그
- [x] API: `GET /feed/live` (커서 기반, type 필터)
- [x] API: `GET /issues/{id}/timeline` (업데이트 타임라인)
- [x] 스케줄러: `news_collect` (15분), `keyword_state_cleanup` (1시간) 잡 등록
- [x] 키워드 상태 관리: ACTIVE → COOLDOWN(48h) → CLOSED(120h) 자동 전환
- [x] 이슈 상태 자동 조정: ONGOING → CLOSED(30일) → REIGNITED(7일 내 재유입)
- [x] 임계값/가중치 설정 분리: `src/core/config.py` 환경변수 오버라이드
- [x] 테스트: 분류기 단위/통합 + 피드 API + 스케줄러 잡 (41개 케이스 통과)
- [x] 멱등성: canonical_url unique + ON CONFLICT DO NOTHING

### 미완료 항목 ❌
- [ ] `GET /feed/top` API (Top Stories 랭킹) + `issue_rank_snapshots` 테이블
- [ ] `issue_keyword_alias` 테이블 (유사 키워드 정규화 매핑)
- [ ] 알림 시스템: `user_alert_rules`, `notifications` 테이블 + MAJOR 발송
- [ ] 키워드 구독: `keywords`, `keyword_matches` 사용자 관심 키워드
- [ ] 품질 게이트 자동화 (JSON 검증, 요약 실패 fallback, 중복 폭주 차단)
- [ ] 운영 이상징후 알림 (수집량 급감, 소스 장애, 모델 실패율)
- [ ] KPI 로그 적재 (`features`, `predicted_label`, `final_label`, `feedback`)
- [ ] `economic_calendar_items` (경제 일정)
