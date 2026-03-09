# ROADMAP (백엔드 API)

> PRD 기반 백엔드 개발 로드맵
> 생성일: 2026-03-09
> 기반 PRD: `trend-korea-api/docs/PRD.md`
> 상위 로드맵: `docs/ROADMAP.md`

## 개요

대한민국 사회 이슈/사건 데이터를 수집, 분류, 요약하여 REST API로 제공하는 FastAPI 백엔드 서비스의 개발 로드맵.

### 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프레임워크 | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy 2.0 (sync) |
| 검증 | Pydantic V2 |
| DB | PostgreSQL 16 |
| 마이그레이션 | Alembic |
| 스케줄러 | APScheduler (BlockingScheduler) |
| AI/LLM | OpenAI API 호환 (Ollama / OpenAI / Gemini) |
| 린터/포매터 | ruff (line-length=100) |
| 패키지 매니저 | uv |

### 테스트 전략

- **프레임워크**: pytest (17개 테스트 파일, 도메인별 구성)
- **테스트 트로피**: Unit 30% / Integration 40% / E2E 10% / Static Analysis 20%
- **Phase 2 이후**: TDD 필수 (Red-Green-Refactor)
- **검증 명령어**: `uv run pytest`, `uv run ruff check src/`, `uv run ruff format src/`

### 현재 상태 (2026-03-09)

MVP 사용자 서비스 API 66개 엔드포인트 구현 완료. 뉴스 수집 파이프라인 및 스케줄러 워커 6개 잡 운영 중. 어드민 API(사건/이슈/트리거/태그/출처 CRUD)는 기존 라우터에 admin 권한 엔드포인트로 구현 완료. 어드민 전용 고도화 API(대시보드, 사용자 관리, 신고, 파이프라인 모니터링)는 독립 프로젝트 `trend-korea-admin`으로 이관됨. 일부 사용자 기능(SNS 실제 연동, 활동 내역, 헬스체크)은 미구현.

---

## Phase 요약

| Phase | 이름 | 설명 | 예상 기간 | TDD | 상태 |
|-------|------|------|-----------|-----|------|
| 1 | MVP 완성 | 미구현 stub API 실제 구현 + 헬스체크 | 1주 | 필수 | ⬜ |
| 2 | ~~어드민 고도화 API~~ | ~~대시보드, 사용자 관리, 신고, 파이프라인 모니터링~~ | ~~2.5주~~ | ~~필수~~ | ❌ [이관됨] |
| 3 | 사용자 서비스 강화 | SSE 피드, 알림, 이미지 업로드, 지표/입법 | 3주 | 필수 | ⬜ |
| 4 | 안정화/성능 | Rate Limiting, 전문 검색, 성능 최적화, 인프라 | 2주 | 필수 | ⬜ |
| 5 | 장기 확장 | 오픈 API, 데이터 내보내기, 생필품 스케줄러 | 장기 | 필수 | ⬜ |

---

## 완료된 기능 (MVP 사용자 서비스)

> 아래 기능은 코드베이스 검증 완료 (2026-03-09 기준)

- [x] `DONE-001` 인증 시스템: 이메일 가입/로그인/로그아웃/회원탈퇴, JWT, SNS 로그인 간소화 (S-API-AUTH-1 ~ S-API-AUTH-7)
- [x] `DONE-002` 사건 CRUD + 저장/해제: admin 생성/수정/삭제, member 저장 (S-API-EVENT-1 ~ S-API-EVENT-7)
- [x] `DONE-003` 이슈 CRUD + 추적/해제 + 트리거 관리 (S-API-ISSUE-1 ~ S-API-ISSUE-10, S-API-TRIGGER-1 ~ S-API-TRIGGER-2)
- [x] `DONE-004` 커뮤니티: 게시글 CRUD, 댓글/대댓글, 추천/비추천, 댓글 좋아요 (S-API-POST-1 ~ S-API-POST-8, S-API-COMMENT-1 ~ S-API-COMMENT-4)
- [x] `DONE-005` 통합 검색: 사건/이슈/게시글 탭별 검색, 페이지 기반 (S-API-SEARCH-1 ~ S-API-SEARCH-4)
- [x] `DONE-006` 내 추적: 추적 이슈/저장 사건 모아보기 (S-API-TRACK-1 ~ S-API-TRACK-2)
- [x] `DONE-007` 사용자 관리: 내 정보 조회/수정, 비밀번호 변경, 공개 프로필 (S-API-USER-1 ~ S-API-USER-3, S-API-USER-7)
- [x] `DONE-008` 홈 데이터: 속보, 인기 게시글, 검색 랭킹, 트렌딩, 미니맵, 주요 뉴스, 미디어 (S-API-HOME-1 ~ S-API-HOME-7)
- [x] `DONE-009` 태그/출처 CRUD (S-API-TAG-1 ~ S-API-TAG-4, S-API-SOURCE-1 ~ S-API-SOURCE-3)
- [x] `DONE-010` 실시간 피드: live_feed_items 기반 (S-API-FEED-1)
- [x] `DONE-011` 뉴스 수집 파이프라인: 키워드 -> 크롤링 -> 분류 -> 요약 -> 피드 (S-JOB-1)
- [x] `DONE-012` 스케줄러 워커: 6개 잡 (S-JOB-1 ~ S-JOB-6)
- [x] `DONE-013` 에러 코드 체계 + 응답 형식 통일
- [x] `DONE-014` 커서/페이지 기반 페이지네이션
- [x] `DONE-015` 백엔드 테스트: 17개 테스트 파일 (도메인별)

---

## Phase 1: MVP 완성 - 미구현 API 실제 구현

**목표**: 현재 stub 상태인 API를 실제 구현하고, 운영에 필요한 헬스체크를 추가한다
**예상 기간**: 1주
**선행 조건**: 없음 (기존 프로젝트 위에 확장)
**TDD**: 필수 (Red-Green-Refactor)

#### 태스크

- [ ] `P1-001` SNS 계정 연동/해제 실제 구현
  - **설명**: 현재 stub 반환 중인 `POST /users/me/social-connect`와 `DELETE /users/me/social-disconnect`를 실제 OAuth 토큰 교환 기반으로 구현한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/utils/social/` — 각 provider별 실제 OAuth 토큰 교환 로직 구현
    - `src/api/v1/users.py` — social-connect/disconnect 엔드포인트 실제 로직 연결
    - `src/crud/users.py` 또는 `src/sql/users.py` — SNS 계정 연결/해제 DB 로직
  - **테스트 (TDD)**:
    - 🔴 카카오 OAuth 토큰 교환 성공 시 `user_social_accounts`에 레코드 생성 테스트
    - 🔴 이미 연동된 provider 재연동 시 409 반환 테스트
    - 🔴 연동 해제 시 해당 레코드 삭제 테스트
    - 🟢 provider별 OAuth 클라이언트 + DB 연동 구현
    - 🔵 provider 어댑터 패턴으로 공통 인터페이스 추출
  - **예상 소요**: 2일
  - **의존성**: 없음
  - **Spec ID**: S-API-USER-4, S-API-USER-5

- [ ] `P1-002` 내 활동 내역 실제 구현
  - **설명**: 현재 빈 배열을 반환하는 `GET /users/me/activity`를 실제 활동 데이터로 구현한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/sql/users.py` — 사용자 활동 집계 쿼리 (작성 게시글 수, 댓글 수, 추천 수, 추적 이슈 수, 저장 사건 수)
    - `src/schemas/users.py` — `UserActivityResponse` 스키마 업데이트
    - `src/api/v1/users.py` — activity 엔드포인트 로직 연결
  - **테스트 (TDD)**:
    - 🔴 게시글 3건, 댓글 5건 작성한 사용자의 activity 응답에 정확한 카운트 반환 테스트
    - 🟢 집계 쿼리 + 응답 스키마 구현
    - 🔵 캐싱 또는 비정규화 카운트 도입 검토
  - **예상 소요**: 1일
  - **의존성**: 없음
  - **Spec ID**: S-API-USER-6

- [ ] `P1-003` 헬스체크 엔드포인트 구현
  - **설명**: Liveness 및 Readiness 헬스체크 엔드포인트를 추가한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/api/v1/health.py` — 헬스체크 라우터
    - `GET /health/live` — 프로세스 활성 확인 (항상 200)
    - `GET /health/ready` — DB 연결 + 필수 서비스 상태 확인
    - `src/main.py` — 라우터 등록
  - **테스트 (TDD)**:
    - 🔴 `/health/live` 호출 시 200 + `{"status": "ok"}` 반환 테스트
    - 🔴 `/health/ready` DB 연결 실패 시 503 반환 테스트
    - 🟢 헬스체크 라우터 구현
    - 🔵 Readiness 체크에 스케줄러 상태 포함 검토
  - **예상 소요**: 0.5일
  - **의존성**: 없음

- [ ] `P1-004` 실제 OAuth 토큰 교환 구현
  - **설명**: 현재 가상 이메일을 생성하는 SNS 로그인을 실제 OAuth 토큰 교환으로 전환한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/utils/social/kakao.py` — 카카오 OAuth 토큰 교환 + 사용자 정보 조회
    - `src/utils/social/naver.py` — 네이버 OAuth 토큰 교환 + 사용자 정보 조회
    - `src/utils/social/google.py` — 구글 OAuth 토큰 교환 + 사용자 정보 조회
    - `src/crud/auth.py` — social-login 로직에서 실제 provider 데이터 사용
  - **테스트 (TDD)**:
    - 🔴 유효한 카카오 code로 로그인 시 사용자 생성 + 토큰 반환 테스트 (provider mock)
    - 🔴 잘못된 code로 로그인 시 401 반환 테스트
    - 🟢 각 provider별 토큰 교환 클라이언트 구현
    - 🔵 httpx AsyncClient 활용, 타임아웃/재시도 로직 추가
  - **예상 소요**: 2일
  - **의존성**: `P1-001`
  - **Spec ID**: S-API-AUTH-6

#### 완료 기준
- `POST /users/me/social-connect`, `DELETE /users/me/social-disconnect`가 실제 OAuth 연동으로 동작한다
- `GET /users/me/activity`가 실제 활동 데이터를 반환한다
- `/health/live`, `/health/ready` 헬스체크가 동작한다
- SNS 로그인이 실제 OAuth 토큰 교환으로 동작한다
- 모든 테스트 통과 (`uv run pytest`)
- 린트 통과 (`uv run ruff check src/`)

---

## ~~Phase 2: 어드민 고도화 API~~ [이관됨]

> **[이관됨] 어드민 관리 기능은 독립 프로젝트 `trend-korea-admin`으로 분리되었습니다.**
> 아래 태스크는 `trend-korea-admin` 프로젝트에서 구현됩니다. 참조용으로 유지합니다.

**~~목표~~**: ~~어드민 대시보드, 사용자 관리, 신고 시스템, 파이프라인 모니터링 백엔드 API를 구현한다~~
**~~예상 기간~~**: ~~2.5주~~
**~~선행 조건~~**: ~~Phase 1~~
**~~TDD~~**: ~~필수 (Red-Green-Refactor)~~

> ~~이 Phase는 루트 ROADMAP의 Phase 4 (어드민 고도화) 백엔드 태스크에 해당한다.~~
> ~~프론트엔드 UI 연동은 루트 ROADMAP에서 관리한다.~~

#### ~~Phase 2-1: 어드민 대시보드 API (FR-AD1)~~ [이관됨] → trend-korea-admin

- [ ] ~~`P2-001` 어드민 라우터 + 대시보드 통계 API~~ [이관됨] → trend-korea-admin
  - **설명**: ~~어드민 전용 라우터를 생성하고, 대시보드에 필요한 통계 API를 구현한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/api/v1/admin.py` — 어드민 전용 라우터 (`prefix="/admin"`, `CurrentAdminUserId` 의존성)~~
    - ~~`src/schemas/admin.py` — `DashboardStatsResponse`, `RecentJobsResponse` 스키마~~
    - ~~`src/sql/admin.py` — 집계 쿼리~~
    - ~~`GET /api/v1/admin/dashboard/stats` — 오늘 등록 사건/트리거 수, 활성 이슈 수, 오늘 가입/활성 사용자 수~~
    - ~~`GET /api/v1/admin/dashboard/recent-jobs` — 최근 잡 실행 이력 (limit 파라미터)~~
    - ~~`src/main.py` — 라우터 등록~~
  - **테스트 (TDD)**:
    - ~~🔴 `/admin/dashboard/stats` 호출 시 올바른 집계 결과 반환 테스트~~
    - ~~🔴 `/admin/dashboard/recent-jobs?limit=5` 호출 시 최근 5건 반환 테스트~~
    - ~~🔴 비어드민 사용자가 호출 시 403 반환 테스트~~
    - ~~🟢 SQL 집계 쿼리 + 라우터 구현~~
    - ~~🔵 쿼리 성능 최적화 (COUNT 쿼리 단일화)~~
  - **예상 소요**: ~~2일~~
  - **의존성**: ~~없음~~
  - **Spec ID**: S-AD1-1, S-AD1-2, S-AD1-3

#### ~~Phase 2-2: 사용자 관리 API (FR-AD4)~~ [이관됨] → trend-korea-admin

- [ ] ~~`P2-002` 사용자 목록 조회 API (admin)~~ [이관됨] → trend-korea-admin
  - **설명**: ~~어드민이 전체 사용자 목록을 조회할 수 있는 API를 구현한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/api/v1/admin.py` — 사용자 목록 엔드포인트 추가~~
    - ~~`src/schemas/admin.py` — `AdminUserListResponse` 스키마 (닉네임, 이메일, 역할, 상태, 가입일)~~
    - ~~`src/sql/admin.py` — 사용자 목록 쿼리 (필터: role, is_active, 검색: nickname/email)~~
    - ~~`GET /api/v1/admin/users` — 페이지 기반 사용자 목록~~
  - **테스트 (TDD)**:
    - ~~🔴 role=member 필터 시 member 사용자만 반환 테스트~~
    - ~~🔴 닉네임 검색 시 부분 일치 결과 반환 테스트~~
    - ~~🟢 필터 + 검색 + 페이지네이션 쿼리 구현~~
    - ~~🔵 인덱스 활용 최적화~~
  - **예상 소요**: ~~1일~~
  - **의존성**: ~~`P2-001`~~
  - **Spec ID**: S-AD4-1

- [ ] ~~`P2-003` 사용자 역할 변경 + 정지/복원 API (admin)~~ [이관됨] → trend-korea-admin
  - **설명**: ~~어드민이 사용자 역할을 변경하거나 계정을 정지/복원할 수 있는 API를 구현한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/api/v1/admin.py` — 역할 변경, 정지/복원 엔드포인트 추가~~
    - ~~`src/sql/admin.py` — 역할 업데이트, is_active 토글 쿼리~~
    - ~~`PATCH /api/v1/admin/users/{id}/role` — 역할 변경 (member <-> admin)~~
    - ~~`PATCH /api/v1/admin/users/{id}/status` — 정지/복원 (`is_active` 토글)~~
  - **테스트 (TDD)**:
    - ~~🔴 비어드민 사용자가 역할 변경 API 호출 시 403 반환 테스트~~
    - ~~🔴 자기 자신의 역할 변경 시도 시 400 반환 테스트~~
    - ~~🔴 정지된 사용자 로그인 시도 시 401 반환 테스트~~
    - ~~🟢 역할 변경 + 정지/복원 로직 구현~~
    - ~~🔵 자기 자신 변경 방지, 마지막 admin 강등 방지 로직~~
  - **예상 소요**: ~~1.5일~~
  - **의존성**: ~~`P2-002`~~
  - **Spec ID**: S-AD4-2, S-AD4-3

#### ~~Phase 2-3: 신고 시스템 (FR-AD5)~~ [이관됨] → trend-korea-admin

- [ ] ~~`P2-004` 신고 데이터 모델 + 마이그레이션~~ [이관됨] → trend-korea-admin
  - **설명**: ~~게시글/댓글 신고를 위한 데이터 모델을 설계하고 Alembic 마이그레이션을 생성한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/models/report.py` — `Report` 모델~~
      - ~~`id: String(36) PK`~~
      - ~~`entity_type: Enum(post|comment)` — 신고 대상 유형~~
      - ~~`entity_id: String(36)` — 신고 대상 ID~~
      - ~~`reporter_id: FK -> users.id` — 신고자~~
      - ~~`reason: Enum(spam|abuse|misinformation|inappropriate|other)` — 신고 사유~~
      - ~~`description: Text NULLABLE` — 상세 설명~~
      - ~~`status: Enum(pending|reviewed|dismissed)` — 처리 상태~~
      - ~~`reviewed_by: FK -> users.id NULLABLE` — 처리 어드민~~
      - ~~`reviewed_at: DateTime(tz) NULLABLE` — 처리 시각~~
      - ~~`created_at: DateTime(tz)` — 신고 시각~~
    - ~~`src/db/enums.py` — `ReportEntityType`, `ReportReason`, `ReportStatus` Enum 추가~~
    - ~~`src/db/__init__.py` — 배럴 import 등록~~
    - ~~Alembic 마이그레이션 생성~~
  - **테스트 (TDD)**:
    - ~~🔴 Report 모델 인스턴스 생성 및 DB 저장 테스트~~
    - ~~🟢 모델 + 마이그레이션 구현~~
    - ~~🔵 UniqueConstraint(entity_type, entity_id, reporter_id) 추가~~
  - **예상 소요**: ~~1일~~
  - **의존성**: ~~없음~~

- [ ] ~~`P2-005` 게시글/댓글 신고 API (member)~~ [이관됨] → trend-korea-admin
  - **설명**: ~~로그인 사용자가 게시글이나 댓글을 신고할 수 있는 API를 구현한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/schemas/report.py` — `ReportCreateRequest`, `ReportResponse` 스키마~~
    - ~~`src/sql/report.py` — 신고 생성, 중복 체크 쿼리~~
    - ~~`src/api/v1/community.py` — 신고 엔드포인트 추가~~
    - ~~`POST /api/v1/posts/{id}/report` — 게시글 신고~~
    - ~~`POST /api/v1/comments/{id}/report` — 댓글 신고~~
  - **테스트 (TDD)**:
    - ~~🔴 게시글 신고 성공 시 201 반환 + DB 레코드 생성 테스트~~
    - ~~🔴 동일 사용자가 같은 게시글 중복 신고 시 409 반환 테스트~~
    - ~~🔴 존재하지 않는 게시글 신고 시 404 반환 테스트~~
    - ~~🟢 신고 생성 로직 + 중복 체크 구현~~
    - ~~🔵 자기 게시글 신고 방지 로직 추가~~
  - **예상 소요**: ~~1.5일~~
  - **의존성**: ~~`P2-004`~~
  - **Spec ID**: S-AD5-1, S-AD5-2

- [ ] ~~`P2-006` 신고 관리 API (admin)~~ [이관됨] → trend-korea-admin
  - **설명**: ~~어드민이 신고된 콘텐츠를 조회하고 처리할 수 있는 API를 구현한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/schemas/admin.py` — `ReportListResponse`, `ReportActionRequest` 스키마~~
    - ~~`src/sql/admin.py` — 신고 목록 쿼리 (필터: status, entity_type)~~
    - ~~`src/api/v1/admin.py` — 신고 관리 엔드포인트 추가~~
    - ~~`GET /api/v1/admin/reports` — 신고 목록 (페이지 기반, 필터: status/entity_type)~~
    - ~~`PATCH /api/v1/admin/reports/{id}` — 신고 처리 (reviewed/dismissed + 선택적 콘텐츠 삭제)~~
  - **테스트 (TDD)**:
    - ~~🔴 pending 필터 시 미처리 신고만 반환 테스트~~
    - ~~🔴 신고 처리(reviewed) 시 status 변경 + reviewed_by/reviewed_at 기록 테스트~~
    - ~~🔴 신고 처리 시 콘텐츠 삭제 옵션 동작 테스트~~
    - ~~🟢 신고 목록 + 처리 로직 구현~~
    - ~~🔵 신고 건수 대시보드 연동 (P2-001 stats에 포함)~~
  - **예상 소요**: ~~1.5일~~
  - **의존성**: ~~`P2-005`~~
  - **Spec ID**: S-AD1-4, S-AD5-3

#### ~~Phase 2-4: 파이프라인 모니터링 API (FR-AD6)~~ [이관됨] → trend-korea-admin

- [ ] ~~`P2-007` 파이프라인 통계 + 키워드 상태 API~~ [이관됨] → trend-korea-admin
  - **설명**: ~~뉴스 수집 파이프라인의 통계와 키워드 상태를 조회하는 API를 구현한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/schemas/admin.py` — `PipelineStatsResponse`, `KeywordStateListResponse` 스키마~~
    - ~~`src/sql/admin.py` — 파이프라인 통계 쿼리 (최근 24시간 수집 기사 수, 요약 수, 분류 결과별 건수)~~
    - ~~`src/api/v1/admin.py` — 파이프라인 모니터링 엔드포인트 추가~~
    - ~~`GET /api/v1/admin/pipeline/stats` — 파이프라인 통계~~
    - ~~`GET /api/v1/admin/pipeline/keyword-states` — 키워드 상태 목록 (페이지 기반, 필터: status)~~
  - **테스트 (TDD)**:
    - ~~🔴 파이프라인 통계 API 호출 시 올바른 집계 결과 반환 테스트~~
    - ~~🔴 키워드 상태 active 필터 시 active 상태만 반환 테스트~~
    - ~~🟢 집계 쿼리 + 라우터 구현~~
    - ~~🔵 통계 캐싱 검토 (빈번한 변경이 아님)~~
  - **예상 소요**: ~~1.5일~~
  - **의존성**: ~~`P2-001`~~
  - **Spec ID**: S-AD6-1, S-AD6-2, S-AD6-3

- [ ] ~~`P2-008` 수동 뉴스 수집 트리거 API~~ [이관됨] → trend-korea-admin
  - **설명**: ~~어드민이 수동으로 뉴스 수집 파이프라인 사이클을 트리거할 수 있는 API를 구현한다~~
  - **영역**: 백엔드
  - **구현 사항**:
    - ~~`src/api/v1/admin.py` — 수동 트리거 엔드포인트~~
    - ~~`POST /api/v1/admin/pipeline/trigger-collect` — 수동 뉴스 수집 트리거~~
    - ~~백그라운드에서 `run_cycle()` 실행 (스레드 또는 BackgroundTask)~~
    - ~~동시 실행 방지 (lock 또는 상태 체크)~~
  - **테스트 (TDD)**:
    - ~~🔴 수동 트리거 호출 시 202 Accepted 반환 테스트~~
    - ~~🔴 이미 실행 중일 때 409 반환 테스트~~
    - ~~🟢 BackgroundTask + 실행 상태 관리 구현~~
    - ~~🔵 실행 진행 상태 조회 API 추가 검토~~
  - **예상 소요**: ~~1.5일~~
  - **의존성**: ~~`P2-007`~~
  - **Spec ID**: S-AD6-4

#### ~~완료 기준~~ [이관됨]
- ~~어드민 대시보드 통계/최근 잡 API가 동작한다~~
- ~~사용자 목록 조회, 역할 변경, 정지/복원이 동작한다~~
- ~~게시글/댓글 신고 생성 및 어드민 처리가 동작한다~~
- ~~파이프라인 통계, 키워드 상태 조회, 수동 수집 트리거가 동작한다~~
- ~~모든 테스트 통과 (`uv run pytest`)~~
- ~~린트 통과 (`uv run ruff check src/`)~~

---

## Phase 3: 사용자 서비스 강화

**목표**: SSE 실시간 피드, 알림 시스템, 이미지 업로드, 지표/입법 데이터 등 사용자 경험을 강화하는 백엔드 API를 구현한다
**예상 기간**: 3주
**선행 조건**: Phase 1
**TDD**: 필수 (Red-Green-Refactor)

> 이 Phase는 루트 ROADMAP의 Phase 5 (사용자 서비스 강화) 백엔드 태스크에 해당한다.
> Phase 2는 `trend-korea-admin`으로 이관되어 이 프로젝트에서는 Phase 1 완료 후 바로 진행 가능하다.

#### Phase 3-1: SSE 실시간 피드

- [ ] `P3-001` SSE 기반 실시간 피드 엔드포인트
  - **설명**: 기존 polling 방식의 피드를 SSE(Server-Sent Events)로 전환한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/api/v1/feed.py` — SSE 엔드포인트 추가
    - `GET /api/v1/feed/stream` — SSE 스트림 (type 파라미터: breaking/major/all)
    - FastAPI `StreamingResponse` + `text/event-stream` Content-Type
    - 피드 이벤트 형식: `data: {"id": "...", "type": "breaking", ...}\n\n`
    - heartbeat 메시지 (30초 간격)
  - **테스트 (TDD)**:
    - 🔴 SSE 연결 시 Content-Type `text/event-stream` 반환 테스트
    - 🔴 heartbeat 메시지가 주기적으로 전송되는지 테스트
    - 🟢 SSE 스트림 생성기 + 엔드포인트 구현
    - 🔵 연결 타임아웃, 재연결 지원 (Last-Event-ID 헤더)
  - **예상 소요**: 2일
  - **의존성**: 없음

#### Phase 3-2: 알림 시스템

- [ ] `P3-002` 알림 데이터 모델 + 마이그레이션
  - **설명**: 사용자 알림 시스템을 위한 데이터 모델을 설계한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/models/notification.py` — `Notification` 모델
      - `id: String(36) PK`
      - `user_id: FK -> users.id` — 알림 수신자
      - `type: Enum(trigger_update|comment_reply|post_like|system)` — 알림 유형
      - `title: String(100)` — 알림 제목
      - `message: Text` — 알림 내용
      - `entity_type: String(20) NULLABLE` — 연관 엔티티 유형
      - `entity_id: String(36) NULLABLE` — 연관 엔티티 ID
      - `is_read: Boolean default=False` — 읽음 여부
      - `created_at: DateTime(tz)` — 생성 시각
    - `src/db/enums.py` — `NotificationType` Enum 추가
    - `src/db/__init__.py` — 배럴 import 등록
    - Alembic 마이그레이션 생성
  - **테스트 (TDD)**:
    - 🔴 Notification 모델 인스턴스 생성 및 DB 저장 테스트
    - 🟢 모델 + 마이그레이션 구현
    - 🔵 인덱스: (user_id, is_read, created_at)
  - **예상 소요**: 1일
  - **의존성**: 없음

- [ ] `P3-003` 알림 생성 로직 + 조회/읽음 API
  - **설명**: 트리거 생성 시 추적자에게 알림을 생성하고, 알림 조회/읽음 처리 API를 구현한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/schemas/notification.py` — `NotificationResponse`, `NotificationListResponse` 스키마
    - `src/sql/notification.py` — 알림 생성, 목록 조회, 읽음 처리 쿼리
    - `src/crud/notification.py` — 알림 생성 비즈니스 로직
    - `src/api/v1/users.py` — 알림 엔드포인트 추가
    - `GET /api/v1/users/me/notifications` — 알림 목록 (페이지 기반, 필터: is_read)
    - `PATCH /api/v1/users/me/notifications/{id}/read` — 읽음 처리
    - `POST /api/v1/users/me/notifications/read-all` — 전체 읽음
    - `src/crud/issues.py` — 트리거 생성 시 추적자 알림 생성 호출 추가
  - **테스트 (TDD)**:
    - 🔴 트리거 생성 시 해당 이슈 추적자에게 알림 생성 테스트
    - 🔴 알림 목록 조회 시 is_read=false 필터 동작 테스트
    - 🔴 읽음 처리 시 is_read 필드 true로 변경 테스트
    - 🔴 전체 읽음 시 해당 사용자의 모든 알림 읽음 처리 테스트
    - 🟢 알림 CRUD + 트리거 연동 구현
    - 🔵 알림 일괄 생성 성능 최적화 (bulk insert)
  - **예상 소요**: 2일
  - **의존성**: `P3-002`

#### Phase 3-3: 이미지 업로드

- [ ] `P3-004` 이미지 업로드 API
  - **설명**: 게시글에 이미지를 첨부할 수 있는 업로드 API를 구현한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/api/v1/uploads.py` — 업로드 라우터
    - `POST /api/v1/uploads/images` — 이미지 업로드 (multipart/form-data)
    - 반환: `{ "url": "/uploads/images/{filename}" }`
    - 파일 크기 제한: 5MB
    - 허용 형식: JPEG, PNG, WebP
    - 스토리지: 로컬 파일시스템 (추상화된 어댑터 패턴으로 S3/R2 전환 가능)
    - `src/utils/storage.py` — `StorageAdapter` 인터페이스 + `LocalStorageAdapter` 구현
    - `src/main.py` — 라우터 등록 + 정적 파일 서빙
  - **테스트 (TDD)**:
    - 🔴 유효한 JPEG 파일 업로드 시 200 + URL 반환 테스트
    - 🔴 5MB 초과 파일 업로드 시 413 반환 테스트
    - 🔴 허용되지 않는 형식(GIF) 업로드 시 400 반환 테스트
    - 🟢 파일 검증 + StorageAdapter + 엔드포인트 구현
    - 🔵 이미지 리사이징/최적화 검토
  - **예상 소요**: 2일
  - **의존성**: 없음
  - [PRD 확인 필요] 이미지 저장소 결정 (S3 / Cloudflare R2 등)

#### Phase 3-4: 지표 데이터

- [ ] `P3-005` 지표 데이터 수집 및 API
  - **설명**: 환율, 주요 경제 지표 등을 수집하고 API로 제공한다
  - **영역**: 백엔드
  - **구현 사항**:
    - 기존 `product_info`/`product_prices` 테이블 활용 또는 새 지표 모델 설계
    - `src/api/v1/home.py` — 지표 엔드포인트 추가
    - `GET /api/v1/home/indicators` — 주요 지표 목록 (최신 값 + 변동률)
    - `src/scheduler/jobs.py` — 지표 데이터 주기적 갱신 잡 등록
  - **테스트 (TDD)**:
    - 🔴 `/home/indicators` 호출 시 지표 목록 반환 테스트
    - 🔴 변동률 계산 로직 테스트 (전일 대비)
    - 🟢 데이터 수집 + API 구현
    - 🔵 캐싱 전략 적용 (지표는 빈번히 변하지 않음)
  - **예상 소요**: 2일
  - **의존성**: 없음
  - [PRD 확인 필요] 수집할 지표 종류와 데이터 소스 결정

#### Phase 3-5: 입법 현황

- [ ] `P3-006` 입법 현황 데이터 수집 및 API
  - **설명**: 국회 입법 현황을 수집하고 요약하여 제공한다
  - **영역**: 백엔드
  - **구현 사항**:
    - 입법 현황 데이터 모델 설계 (법안명, 발의일, 상태, 소관위 등)
    - `src/utils/legislation_crawler/` — 국회 공공 API 연동 크롤러
    - `src/api/v1/home.py` — 입법 현황 엔드포인트 추가
    - `GET /api/v1/home/legislation` — 입법 현황 목록
    - 스케줄러 잡 등록 (일 1회 갱신)
  - **테스트 (TDD)**:
    - 🔴 `/home/legislation` 호출 시 입법 현황 목록 반환 테스트
    - 🟢 데이터 수집 + API 구현
    - 🔵 데이터 캐싱, 갱신 주기 최적화
  - **예상 소요**: 3일
  - **의존성**: 없음
  - [PRD 확인 필요] 데이터 소스(국회 공공 API) 및 범위 결정

#### 완료 기준
- SSE 실시간 피드 스트림이 동작한다
- 트리거 생성 시 추적자에게 알림이 생성되고, 조회/읽음 처리가 동작한다
- 이미지 업로드가 동작하고 스토리지 어댑터가 교체 가능하다
- 지표 데이터 및 입법 현황 API가 동작한다
- 모든 테스트 통과 (`uv run pytest`)

---

## Phase 4: 안정화 및 성능 최적화

**목표**: Rate Limiting, 전문 검색, 성능 최적화, 인프라 기반을 구축한다
**예상 기간**: 2주
**선행 조건**: Phase 1
**TDD**: 필수

#### 태스크

- [ ] `P4-001` Rate Limiting 적용
  - **설명**: 인증 엔드포인트에 Rate Limiting을 적용하여 brute force 공격을 방지한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/core/rate_limit.py` — Rate Limiting 미들웨어 또는 의존성
    - 인증 엔드포인트: 5회/분 (IP 기반)
    - 일반 API: 60회/분 (사용자 기반)
    - `slowapi` 또는 커스텀 구현 (인메모리 또는 Redis)
  - **테스트 (TDD)**:
    - 🔴 로그인 6회 연속 호출 시 429 반환 테스트
    - 🟢 Rate Limiter 구현 + 미들웨어 적용
    - 🔵 Redis 기반으로 전환 가능하도록 어댑터 패턴 적용
  - **예상 소요**: 2일
  - **의존성**: 없음

- [ ] `P4-002` 전문 검색 개선 (PostgreSQL FTS)
  - **설명**: 현재 LIKE 기반 검색을 PostgreSQL Full-Text Search로 개선한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/sql/search.py` — FTS 쿼리로 전환
    - events, issues, posts 테이블에 `tsvector` 컬럼 및 GIN 인덱스 추가
    - Alembic 마이그레이션 생성
    - 한국어 형태소 분석 설정 (pg_bigm 또는 unaccent + simple)
  - **테스트 (TDD)**:
    - 🔴 한글 키워드 검색 시 관련 결과 반환 테스트
    - 🔴 부분 문자열 매칭 동작 테스트
    - 🟢 FTS 쿼리 + 인덱스 구현
    - 🔵 검색 결과 관련도 정렬 개선
  - **예상 소요**: 3일
  - **의존성**: 없음

- [ ] `P4-003` API 응답 성능 최적화
  - **설명**: N+1 쿼리 문제, 불필요한 조인, 느린 쿼리를 식별하고 최적화한다
  - **영역**: 백엔드
  - **구현 사항**:
    - SQLAlchemy 쿼리 로깅 활성화 + 느린 쿼리 분석
    - `selectinload`/`joinedload` 전략 최적화
    - 집계 쿼리 캐싱 (홈 데이터 등)
    - DB 인덱스 점검 및 추가
  - **테스트 (TDD)**:
    - 🔴 대량 데이터(1000건) 환경에서 API 응답 시간 500ms 이내 테스트
    - 🟢 쿼리 최적화 적용
    - 🔵 프로파일링 결과 기반 추가 최적화
  - **예상 소요**: 2일
  - **의존성**: 없음

- [ ] `P4-004` Docker 컨테이너화 + docker-compose
  - **설명**: API 서버, 워커, PostgreSQL을 Docker로 컨테이너화한다
  - **영역**: 인프라
  - **구현 사항**:
    - `Dockerfile` — API 서버 + 워커 멀티스테이지 빌드
    - `docker-compose.yml` — api + worker + postgres 서비스 구성
    - `.dockerignore` — 불필요한 파일 제외
    - 환경변수 관리 (`.env.example`)
  - **테스트 (TDD)**:
    - 🔴 `docker-compose up` 후 `/health/live` 200 응답 테스트
    - 🟢 Dockerfile + docker-compose 구성
    - 🔵 이미지 크기 최적화, 빌드 캐시 활용
  - **예상 소요**: 2일
  - **의존성**: `P1-003` (헬스체크)

- [ ] `P4-005` CI 파이프라인 구축
  - **설명**: GitHub Actions 기반 CI 파이프라인을 구축한다
  - **영역**: 인프라
  - **구현 사항**:
    - `.github/workflows/ci.yml` — CI 워크플로우
    - 단계: ruff check -> ruff format --check -> pytest
    - PostgreSQL 서비스 컨테이너 설정
    - PR 트리거 + main 브랜치 push 트리거
  - **테스트 (TDD)**:
    - 🔴 린트 에러가 있는 코드 push 시 CI 실패 테스트
    - 🟢 GitHub Actions 워크플로우 구성
    - 🔵 테스트 커버리지 리포트 추가
  - **예상 소요**: 1일
  - **의존성**: 없음

#### 완료 기준
- 인증 엔드포인트에 Rate Limiting이 적용되어 있다
- 검색이 PostgreSQL FTS로 동작한다
- API 응답 시간 P95가 500ms 이내이다
- Docker로 전체 서비스가 구동 가능하다
- GitHub Actions CI가 동작한다
- 모든 테스트 통과

---

## Phase 5: 장기 확장

**목표**: 오픈 API, 데이터 내보내기, 생필품 가격 스케줄러 등 서비스를 확장한다
**예상 기간**: 장기 (기능별 우선순위에 따라 진행)
**선행 조건**: Phase 1 이상
**TDD**: 필수

#### 태스크

- [ ] `P5-001` AI 이슈 자동 요약
  - **설명**: OpenAI API를 활용하여 이슈의 트리거 히스토리를 자동 요약한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/utils/issue_summarizer.py` — 이슈 요약 생성 로직
    - `src/api/v1/issues.py` — 이슈 요약 엔드포인트 (`GET /api/v1/issues/{id}/summary`)
    - 스케줄러 잡 또는 트리거 생성 시 자동 요약 갱신
    - `issues` 테이블에 `ai_summary: Text NULLABLE` 필드 추가
  - **테스트 (TDD)**: 요약 생성 로직 단위 테스트, API 통합 테스트
  - **예상 소요**: 3일
  - **의존성**: 없음

- [ ] `P5-002` 오픈 API + API 키 관리
  - **설명**: 외부 개발자가 사건/이슈 데이터를 활용할 수 있는 공개 API를 제공한다
  - **영역**: 백엔드
  - **구현 사항**:
    - API 키 모델 (`api_keys` 테이블)
    - API 키 인증 미들웨어
    - Rate Limiting (API 키 기반)
    - 공개 API 라우터 (`/api/public/v1/`)
  - **테스트 (TDD)**: API 키 인증 테스트, Rate Limiting 테스트
  - **예상 소요**: 3일
  - **의존성**: `P4-001`

- [ ] `P5-003` 데이터 내보내기 (CSV/JSON)
  - **설명**: 사건/이슈 데이터를 CSV 또는 JSON 형식으로 다운로드할 수 있는 API를 구현한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `GET /api/v1/events/export?format=csv|json` — 사건 데이터 내보내기
    - `GET /api/v1/issues/export?format=csv|json` — 이슈 데이터 내보내기
    - StreamingResponse로 대용량 데이터 처리
  - **테스트 (TDD)**: CSV/JSON 직렬화 테스트, 대용량 데이터 스트리밍 테스트
  - **예상 소요**: 2일
  - **의존성**: 없음

- [ ] `P5-004` 생필품 가격 스케줄러 잡 + API
  - **설명**: 기존 생필품 크롤러를 스케줄러에 등록하고, 가격 조회 API를 구현한다
  - **영역**: 백엔드
  - **구현 사항**:
    - `src/scheduler/jobs.py` — 생필품 가격 수집 잡 등록 (일 1회)
    - `src/api/v1/home.py` — 생필품 가격 엔드포인트
    - `GET /api/v1/home/product-prices` — 주요 생필품 최신 가격
  - **테스트 (TDD)**: 가격 조회 API 테스트, 스케줄러 잡 등록 테스트
  - **예상 소요**: 2일
  - **의존성**: 없음

- [ ] `P5-005` 팔로우/구독 시스템 API
  - **설명**: 사용자 간 팔로우 기능과 팔로우한 사용자의 활동 피드 API를 구현한다
  - **영역**: 백엔드
  - **구현 사항**:
    - 팔로우 모델 (`user_follows` 테이블)
    - `POST/DELETE /api/v1/users/{id}/follow` — 팔로우/언팔로우
    - `GET /api/v1/users/me/following` — 팔로잉 목록
    - `GET /api/v1/users/me/feed` — 팔로잉 활동 피드
  - **테스트 (TDD)**: 팔로우/언팔로우 테스트, 피드 정렬 테스트
  - **예상 소요**: 3일
  - **의존성**: 없음

#### 완료 기준
- 각 기능이 독립적으로 배포 가능한 상태이다
- 모든 기능에 테스트가 포함되어 있다

---

## 의존성 그래프

```
Phase 1 (MVP 완성)
  ├── P1-001 SNS 연동 → P1-004 실제 OAuth
  ├── P1-002 활동 내역 (독립)
  └── P1-003 헬스체크 (독립) → P4-004 Docker
        │
        ├── Phase 2 (어드민 고도화 API) ── [이관됨] → trend-korea-admin
        │     ├── (P2-1: 대시보드)
        │     ├── (P2-2: 사용자 관리)
        │     ├── (P2-3: 신고)
        │     └── (P2-4: 파이프라인)
        │
        └── Phase 3 (사용자 서비스 강화) ── Phase 1 완료 후 시작 가능
              ├── P3-1: SSE 피드 (P3-001, 독립)
              ├── P3-2: 알림 (P3-002 → P3-003)
              ├── P3-3: 이미지 업로드 (P3-004, 독립)
              ├── P3-4: 지표 (P3-005, 독립)
              └── P3-5: 입법 (P3-006, 독립)

Phase 4 (안정화/성능) ── Phase 1 완료 후 언제든 시작 가능
  ├── P4-001 Rate Limiting (독립)
  ├── P4-002 전문 검색 (독립)
  ├── P4-003 성능 최적화 (독립)
  ├── P4-004 Docker (P1-003 의존)
  └── P4-005 CI (독립)

Phase 5 (확장) ── Phase 1 완료 후 언제든 시작 가능
  P5-001 ~ P5-005 (각각 독립적)
```

---

## 리스크 및 고려사항

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|----------|
| 실제 OAuth 토큰 교환 시 각 provider API 변경 가능성 | 중간 | provider별 어댑터 패턴으로 격리, 단위 테스트에서 mock 사용 |
| 신고 시스템 DB 스키마 추가 (Alembic 마이그레이션) | 중간 | 별도 마이그레이션으로 분리, 롤백 플랜 준비 |
| SSE 실시간 피드 확장성 (동시 연결 수 제한) | 낮음 | 초기에는 SSE로 충분, 트래픽 증가 시 WebSocket 또는 Redis Pub/Sub 전환 |
| PostgreSQL FTS 한국어 지원 한계 | 중간 | pg_bigm 확장 또는 trigram 인덱스 활용, 장기적으로 Elasticsearch 검토 |
| 이미지 저장소 미결정 (로컬 vs S3/R2) | 낮음 | StorageAdapter 패턴으로 추상화하여 교체 가능하게 구현 |
| 배포 인프라 미결정 | 높음 | Phase 4에서 Docker 컨테이너화 완료 후 VPS/Cloud Run 결정 |
| 지표/입법 외부 API 안정성 | 중간 | API 호출 실패 시 graceful degradation, 캐시 데이터 반환 |
| 알림 대량 생성 시 성능 (인기 이슈 추적자 다수) | 중간 | bulk insert + 비동기 처리 (BackgroundTask) |

---

## PRD 추적성 매트릭스

| PRD 요구사항 | Spec ID | 태스크 ID | Phase | 상태 |
|-------------|---------|----------|-------|------|
| 인증 - 회원가입/로그인/로그아웃/회원탈퇴 | S-API-AUTH-1 ~ 5, 7 | `DONE-001` | MVP | ✅ |
| 인증 - SNS 로그인 (간소화) | S-API-AUTH-6 | `DONE-001` | MVP | ✅ |
| 인증 - 실제 OAuth 토큰 교환 | S-API-AUTH-6 | `P1-004` | 1 | ⬜ |
| 사용자 - 내 정보 조회/수정/비밀번호 변경 | S-API-USER-1 ~ 3 | `DONE-007` | MVP | ✅ |
| 사용자 - SNS 연동/해제 | S-API-USER-4, 5 | `P1-001` | 1 | ⬜ |
| 사용자 - 활동 내역 | S-API-USER-6 | `P1-002` | 1 | ⬜ |
| 사용자 - 공개 프로필 | S-API-USER-7 | `DONE-007` | MVP | ✅ |
| 사건 CRUD + 저장/해제 | S-API-EVENT-1 ~ 7 | `DONE-002` | MVP | ✅ |
| 이슈 CRUD + 추적/해제 + 트리거 | S-API-ISSUE-1 ~ 10, S-API-TRIGGER-1 ~ 2 | `DONE-003` | MVP | ✅ |
| 커뮤니티 - 게시글/댓글 CRUD | S-API-POST-1 ~ 8, S-API-COMMENT-1 ~ 4 | `DONE-004` | MVP | ✅ |
| 검색 - 통합 검색 | S-API-SEARCH-1 ~ 4 | `DONE-005` | MVP | ✅ |
| 내 추적 - 모아보기 | S-API-TRACK-1 ~ 2 | `DONE-006` | MVP | ✅ |
| 홈 - 속보/인기/검색순위/트렌드/미니맵/뉴스/미디어 | S-API-HOME-1 ~ 7 | `DONE-008` | MVP | ✅ |
| 태그/출처 CRUD | S-API-TAG-1 ~ 4, S-API-SOURCE-1 ~ 3 | `DONE-009` | MVP | ✅ |
| 실시간 피드 (polling) | S-API-FEED-1 | `DONE-010` | MVP | ✅ |
| 뉴스 수집 파이프라인 | S-JOB-1 | `DONE-011` | MVP | ✅ |
| 스케줄러 워커 (6개 잡) | S-JOB-1 ~ 6 | `DONE-012` | MVP | ✅ |
| 헬스체크 | — | `P1-003` | 1 | ⬜ |
| ~~어드민 - 대시보드 통계~~ | S-AD1-1 ~ 3 | ~~`P2-001`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| ~~어드민 - 최근 신고~~ | S-AD1-4 | ~~`P2-006`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| ~~어드민 - 사용자 목록 조회~~ | S-AD4-1 | ~~`P2-002`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| ~~어드민 - 역할 변경/정지~~ | S-AD4-2, 3 | ~~`P2-003`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| 어드민 - 게시글/댓글 삭제 (admin) | S-AD5-1, 2 | `DONE-004` | MVP | ✅ |
| ~~어드민 - 신고 시스템~~ | S-AD5-3 | ~~`P2-004` ~ `P2-006`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| ~~어드민 - 파이프라인 통계~~ | S-AD6-1, 2 | ~~`P2-007`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| ~~어드민 - 키워드 상태~~ | S-AD6-3 | ~~`P2-007`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| ~~어드민 - 수동 수집 트리거~~ | S-AD6-4 | ~~`P2-008`~~ | ~~2~~ | ❌ [이관됨] → trend-korea-admin |
| SSE 실시간 피드 | — | `P3-001` | 3 | ⬜ |
| 알림 시스템 | — | `P3-002`, `P3-003` | 3 | ⬜ |
| 이미지 업로드 | — | `P3-004` | 3 | ⬜ |
| 지표 데이터 | — | `P3-005` | 3 | ⬜ |
| 입법 현황 | — | `P3-006` | 3 | ⬜ |
| Rate Limiting | — | `P4-001` | 4 | ⬜ |
| 전문 검색 (FTS) | — | `P4-002` | 4 | ⬜ |
| 성능 최적화 (API P95 < 500ms) | — | `P4-003` | 4 | ⬜ |
| Docker 컨테이너화 | — | `P4-004` | 4 | ⬜ |
| CI 파이프라인 | — | `P4-005` | 4 | ⬜ |
| AI 이슈 자동 요약 | — | `P5-001` | 5 | ⬜ |
| 오픈 API | — | `P5-002` | 5 | ⬜ |
| 데이터 내보내기 | — | `P5-003` | 5 | ⬜ |
| 생필품 가격 스케줄러 + API | — | `P5-004` | 5 | ⬜ |
| 팔로우/구독 | — | `P5-005` | 5 | ⬜ |

---

> **완성도**: 백엔드 PRD 기반 개발 로드맵 (2026-03-09 코드베이스 실사 반영)
