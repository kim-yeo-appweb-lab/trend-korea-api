# 트렌드 코리아 API 백엔드 PRD

> 상태: 확정 | 작성일: 2026-03-09 | 코드베이스 실사 기반

> **참고**: 어드민 관리 기능은 독립 프로젝트 `trend-korea-admin`으로 분리되었습니다.
> 어드민은 Prisma ORM으로 동일 DB에 직접 접근하며, 이 API 서버의 admin 엔드포인트는 하위 호환용으로 유지됩니다.
> 어드민 상세 명세: [`trend-korea-admin/docs/PRD.md`](../../trend-korea-admin/docs/PRD.md)

---

## 1. 제품 정의 (WHY)

### 1.1 한 줄 정의

대한민국 사회 이슈/사건 데이터를 수집, 분류, 요약하여 REST API로 제공하는 FastAPI 백엔드 서비스

### 1.2 해결하는 문제

- 뉴스가 여러 매체에 흩어져 있어 자동 수집/정규화 파이프라인이 필요하다
- 수집된 뉴스 기사의 중복 제거, 분류, 요약을 자동화해야 한다
- 사건/이슈 데이터를 구조화하여 프론트엔드에 일관된 API로 제공해야 한다
- 사용자 인증, 커뮤니티, 검색 등 서비스 핵심 기능의 비즈니스 로직을 처리해야 한다

### 1.3 핵심 가치

| 가치 | 설명 | 측정 지표 |
|------|------|----------|
| 데이터 수집 자동화 | 뉴스 키워드 크롤링 - 기사 수집 - 분류 - 요약 전체 파이프라인 | 15분당 수집 기사 수, 요약 성공률 |
| 안정적 API 제공 | 66개 엔드포인트를 통한 프론트엔드 데이터 서빙 | API 응답 시간 P95 < 500ms |
| 인증/인가 체계 | JWT 기반 인증 + 역할 기반 권한 관리 | 인증 관련 에러율 < 1% |

### 1.4 성공 지표

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| API 응답 시간 (P95) | < 500ms | 서버 로그 기반 |
| DB 쿼리 시간 (P95) | < 100ms | SQLAlchemy 로깅 |
| 뉴스 수집 파이프라인 성공률 | > 90% | `job_runs` 테이블 집계 |
| 스케줄러 잡 실행률 | 100% | `job_runs` 테이블 집계 |

---

## 2. 아키텍처 (HOW)

### 2.1 5레이어 구조

```
api/v1/{domain}.py      # 라우터: HTTP 요청/응답 매핑, 인증 체크, 에러 핸들링
       |
schemas/{domain}.py      # 스키마: Pydantic V2 요청/응답 모델, 필드 검증
       |
crud/{domain}.py         # 비즈니스 로직: 유효성 검증, 조합, 트랜잭션 관리
       |
sql/{domain}.py          # 데이터 액세스: SQLAlchemy 쿼리, 페이지네이션
       |
models/{domain}.py       # 모델: SQLAlchemy ORM 모델, 관계 정의
```

**도메인별 파일 구성**:

| 도메인 | 라우터 | 스키마 | CRUD | SQL | 모델 |
|--------|--------|--------|------|-----|------|
| auth | `api/v1/auth.py` | `schemas/auth.py` | `crud/auth.py` | `sql/auth.py` | `models/auth.py` |
| users | `api/v1/users.py` | `schemas/users.py` | - | `sql/users.py` | `models/users.py` |
| events | `api/v1/events.py` | `schemas/events.py` | `crud/events.py` | `sql/events.py` | `models/events.py` |
| issues | `api/v1/issues.py` | `schemas/issues.py` | `crud/issues.py` | `sql/issues.py` | `models/issues.py` |
| triggers | `api/v1/triggers.py` | `schemas/triggers.py` | - | `sql/triggers.py` | `models/triggers.py` |
| community | `api/v1/community.py` | `schemas/community.py` | `crud/community.py` | `sql/community.py` | `models/community.py` |
| search | `api/v1/search.py` | `schemas/search.py` | `crud/search.py` | `sql/search.py` | `models/search.py` |
| tracking | `api/v1/tracking.py` | `schemas/tracking.py` | `crud/tracking.py` | - | - |
| home | `api/v1/home.py` | - | - | `sql/home.py` | - |
| tags | `api/v1/tags.py` | `schemas/tags.py` | - | `sql/tags.py` | `models/tags.py` |
| sources | `api/v1/sources.py` | `schemas/sources.py` | - | `sql/sources.py` | `models/sources.py` |
| feed | `api/v1/feed.py` | `schemas/feed.py` | `crud/feed.py` | `sql/feed.py` | - |

### 2.2 공유 레이어

```
core/
├── config.py          # pydantic-settings 기반 Settings (환경변수 관리)
├── security.py        # 비밀번호 해싱 (bcrypt), JWT 생성/검증 (HS256)
├── exceptions.py      # AppError (code, message, status_code, details)
├── response.py        # success_response / error_response 유틸
├── pagination.py      # 커서 인코딩/디코딩 (base64 기반 offset)
└── logging.py         # 로깅 설정

db/
├── base.py            # SQLAlchemy DeclarativeBase
├── session.py         # 엔진/세션 팩토리 (SessionLocal, get_db)
├── enums.py           # 공유 Enum (13개)
├── __init__.py        # 모든 모델 배럴 import (Alembic 자동 감지용)
└── {pipeline}.py      # 파이프라인 전용 모델 (11개 파일)

utils/
├── dependencies.py    # FastAPI 의존성 (DbSession, CurrentMemberUserId, CurrentAdminUserId)
├── error_handlers.py  # 글로벌 예외 핸들러
├── social/            # SNS OAuth 인증
├── keyword_crawler/   # 트렌드 키워드 수집
├── news_crawler/      # 뉴스 기사 크롤링
├── naver_news_crawler/# 네이버 뉴스 검색 API
├── news_summarizer/   # LLM 기반 뉴스 요약
├── product_crawler/   # 생필품 가격 크롤러
└── pipeline/          # 전체 파이프라인 오케스트레이터
```

### 2.3 의존성 주입 패턴

`Annotated` + `Depends`를 사용한 3단계 인증 체계:

```python
DbSession = Annotated[Session, Depends(get_db_session)]        # DB 세션
CurrentUserId = Annotated[str, Depends(get_current_user_id)]    # 로그인 사용자
CurrentMemberUserId = Annotated[str, Depends(_require_member_or_admin)]  # member 이상
CurrentAdminUserId = Annotated[str, Depends(_require_admin)]    # admin 전용
```

**인증 흐름**:
1. `Authorization: Bearer <token>` 헤더에서 JWT 추출
2. `decode_token()`으로 payload 검증 (`typ=access` 확인)
3. `sub` 클레임에서 `user_id` 추출
4. DB에서 사용자 존재 여부 확인
5. `request.state.user_id`, `request.state.user_role` 설정

### 2.4 에러 처리 체계

**AppError 구조**:
```python
@dataclass(slots=True)
class ErrorDetail:
    code: str          # "E_{DOMAIN}_{번호}" 형식
    message: str       # 사람이 읽을 수 있는 메시지
    details: dict | None  # 추가 컨텍스트 (field 등)
```

**에러 코드 체계**:

| 접두사 | 용도 | 예시 |
|--------|------|------|
| `E_AUTH_` | 인증 | `E_AUTH_001` (토큰 없음), `E_AUTH_002` (만료), `E_AUTH_003` (유효하지 않음) |
| `E_PERM_` | 권한 | `E_PERM_001` (member 이상 필요), `E_PERM_002` (admin 필요) |
| `E_VALID_` | 검증 | `E_VALID_002` (잘못된 vote_type) |
| `E_RESOURCE_` | 리소스 미존재 | `001` (사건), `002` (이슈), `003` (게시글), `004` (댓글), `005` (사용자/트리거), `006` (태그), `007` (출처) |
| `E_CONFLICT_` | 충돌 | `001` (이메일 중복), `002` (닉네임/이슈 추적 중복), `003` (사건 저장 중복) |
| `E_SERVER_` | 서버 내부 | - |

---

## 3. 도메인 모델 상세 (WHAT)

### 3.1 핵심 엔티티

#### Event (사건) -- `events`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `occurred_at` | `DateTime(tz)` | NOT NULL, INDEX | 발생 일시 |
| `title` | `String(50)` | NOT NULL | 제목 |
| `summary` | `Text` | NOT NULL | 2-3줄 요약 |
| `importance` | `Enum(Importance)` | NOT NULL | low / medium / high |
| `verification_status` | `Enum(VerificationStatus)` | NOT NULL, default=UNVERIFIED | verified / unverified |
| `source_count` | `Integer` | NOT NULL, default=0 | 비정규화 출처 수 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

#### Issue (이슈) -- `issues`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `title` | `String(50)` | NOT NULL | 제목 |
| `description` | `Text` | NOT NULL | 이슈 설명 |
| `status` | `Enum(IssueStatus)` | NOT NULL, INDEX | ongoing / closed / reignited / unverified |
| `tracker_count` | `Integer` | NOT NULL, default=0, INDEX | 비정규화 추적자 수 |
| `latest_trigger_at` | `DateTime(tz)` | NULLABLE, INDEX | 최근 트리거 시점 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

#### Trigger (트리거) -- `triggers`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `issue_id` | `FK -> issues.id` | NOT NULL, INDEX, CASCADE | 소속 이슈 |
| `occurred_at` | `DateTime(tz)` | NOT NULL, INDEX | 발생 일시 |
| `summary` | `Text` | NOT NULL | 트리거 요약 |
| `type` | `Enum(TriggerType)` | NOT NULL | article / ruling / announcement / correction / status_change |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

#### User (사용자) -- `users`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `nickname` | `String(50)` | NOT NULL, UNIQUE, INDEX | 닉네임 |
| `email` | `String(255)` | NOT NULL, UNIQUE, INDEX | 이메일 |
| `password_hash` | `String(255)` | NOT NULL | bcrypt 해시 |
| `profile_image` | `String(500)` | NULLABLE | 프로필 이미지 URL |
| `role` | `Enum(UserRole)` | NOT NULL, default=MEMBER | guest / member / admin |
| `is_active` | `Boolean` | NOT NULL, default=True | 활성 상태 |
| `withdrawn_at` | `DateTime(tz)` | NULLABLE | 탈퇴 일시 (soft delete) |
| `created_at` | `DateTime(tz)` | NOT NULL | 가입 일시 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

#### UserSocialAccount -- `user_social_accounts`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `user_id` | `FK -> users.id` | NOT NULL, INDEX, CASCADE | 소속 사용자 |
| `provider` | `String(20)` | NOT NULL | kakao / naver / google |
| `provider_user_id` | `String(100)` | NOT NULL | SNS 사용자 ID |
| `email` | `String(255)` | NULLABLE | SNS 이메일 |
| `created_at` | `DateTime(tz)` | NOT NULL | 연동 일시 |

#### Post (게시글) -- `posts`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `author_id` | `FK -> users.id` | NOT NULL, INDEX, CASCADE | 작성자 |
| `title` | `String(100)` | NOT NULL | 제목 |
| `content` | `Text` | NOT NULL | 본문 (마크다운) |
| `is_anonymous` | `Boolean` | NOT NULL, default=False | 익명 여부 |
| `like_count` | `Integer` | NOT NULL, default=0 | 추천 수 |
| `dislike_count` | `Integer` | NOT NULL, default=0 | 비추천 수 |
| `comment_count` | `Integer` | NOT NULL, default=0 | 댓글 수 |
| `created_at` | `DateTime(tz)` | NOT NULL, INDEX | 작성 일시 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

**관계**: `author: Mapped["User"]` (lazy="joined")

#### Comment (댓글) -- `comments`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `post_id` | `FK -> posts.id` | NOT NULL, INDEX, CASCADE | 소속 게시글 |
| `parent_id` | `FK -> comments.id` | NULLABLE, CASCADE | 부모 댓글 (대댓글) |
| `author_id` | `FK -> users.id` | NOT NULL, CASCADE | 작성자 |
| `content` | `Text` | NOT NULL | 댓글 내용 |
| `like_count` | `Integer` | NOT NULL, default=0 | 좋아요 수 |
| `created_at` | `DateTime(tz)` | NOT NULL, INDEX | 작성 일시 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

#### Tag (태그) -- `tags`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `name` | `String(50)` | NOT NULL | 태그명 |
| `type` | `Enum(TagType)` | NOT NULL | category / region |
| `slug` | `String(80)` | NOT NULL, UNIQUE, INDEX | URL-safe 식별자 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

#### Source (출처) -- `sources`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `entity_type` | `Enum(SourceEntityType)` | NOT NULL, INDEX | event / issue / trigger |
| `entity_id` | `String(36)` | NOT NULL, INDEX | 다형성 FK |
| `url` | `String(500)` | NOT NULL | 출처 URL |
| `title` | `String(255)` | NOT NULL | 출처 제목 |
| `publisher` | `String(100)` | NOT NULL | 매체명 |
| `published_at` | `DateTime(tz)` | NOT NULL | 발행 일시 |

#### SearchRanking -- `search_rankings`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `keyword` | `String(100)` | NOT NULL, INDEX | 검색 키워드 |
| `rank` | `Integer` | NOT NULL | 순위 (1~10) |
| `score` | `Integer` | NOT NULL | 점수 (빈도) |
| `calculated_at` | `DateTime(tz)` | NOT NULL, INDEX | 산출 시각 |

#### SearchHistory -- `search_histories`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `user_id` | `String(36)` | NOT NULL, INDEX | 사용자 ID |
| `keyword` | `String(100)` | NOT NULL | 검색어 |
| `created_at` | `DateTime(tz)` | NOT NULL, INDEX | 검색 시각 |

#### RefreshToken -- `refresh_tokens`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `user_id` | `FK -> users.id` | NOT NULL, INDEX, CASCADE | 소속 사용자 |
| `token_hash` | `String(64)` | NOT NULL, UNIQUE, INDEX | SHA-256 해시 |
| `jti` | `String(36)` | NOT NULL, UNIQUE, INDEX | JWT ID (고유 식별자) |
| `expires_at` | `DateTime(tz)` | NOT NULL | 만료 시각 |
| `revoked_at` | `DateTime(tz)` | NULLABLE | 폐기 시각 |
| `created_at` | `DateTime(tz)` | NOT NULL | 발급 시각 |

### 3.2 투표/좋아요 테이블

#### PostVote -- `post_votes`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `post_id` | `FK -> posts.id` | NOT NULL, INDEX, CASCADE | 대상 게시글 |
| `user_id` | `FK -> users.id` | NOT NULL, INDEX, CASCADE | 투표 사용자 |
| `vote_type` | `String(10)` | NOT NULL | like / dislike |
| `created_at` | `DateTime(tz)` | NOT NULL | 투표 시각 |

**제약**: `UniqueConstraint("post_id", "user_id", name="uq_post_vote_user")`

#### CommentLike -- `comment_likes`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `comment_id` | `FK -> comments.id` | NOT NULL, INDEX, CASCADE | 대상 댓글 |
| `user_id` | `FK -> users.id` | NOT NULL, INDEX, CASCADE | 좋아요 사용자 |
| `created_at` | `DateTime(tz)` | NOT NULL | 좋아요 시각 |

**제약**: `UniqueConstraint("comment_id", "user_id", name="uq_comment_like_user")`

### 3.3 연관 테이블 (Many-to-Many)

| 테이블 | 관계 | PK 컬럼 | 추가 컬럼 | ondelete |
|--------|------|---------|----------|----------|
| `event_tags` | Event <-> Tag | `event_id`, `tag_id` | - | CASCADE |
| `issue_tags` | Issue <-> Tag | `issue_id`, `tag_id` | - | CASCADE |
| `issue_events` | Issue <-> Event | `issue_id`, `event_id` | - | CASCADE |
| `post_tags` | Post <-> Tag | `post_id`, `tag_id` | - | CASCADE |
| `user_saved_events` | User <-> Event | `user_id`, `event_id` | `saved_at: DateTime(tz)` | CASCADE |
| `user_tracked_issues` | User <-> Issue | `user_id`, `issue_id` | `tracked_at: DateTime(tz)` | CASCADE |

### 3.4 파이프라인 테이블

#### RawArticle -- `raw_articles`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `canonical_url` | `String(2000)` | NOT NULL, UNIQUE, INDEX | 정규화된 URL |
| `original_url` | `String(2000)` | NOT NULL | 원본 URL |
| `title` | `String(500)` | NOT NULL | 기사 제목 |
| `content_text` | `Text` | NULLABLE | 기사 본문 |
| `source_name` | `String(100)` | NULLABLE | 매체명 |
| `title_hash` | `String(64)` | NOT NULL, INDEX | 제목 해시 (중복 탐지) |
| `semantic_hash` | `String(64)` | NOT NULL, INDEX | 의미 해시 (중복 탐지) |
| `entity_json` | `JSON` | NULLABLE | 추출된 엔티티 |
| `normalized_keywords` | `JSON` | NULLABLE | 정규화된 키워드 |
| `keyword_score` | `Float` | NULLABLE | 키워드 점수 |
| `published_at` | `DateTime(tz)` | NULLABLE, INDEX | 발행 일시 |
| `fetched_at` | `DateTime(tz)` | NOT NULL | 수집 일시 |
| `created_at` | `DateTime(tz)` | NOT NULL | DB 저장 일시 |

#### EventUpdate -- `event_updates`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `issue_id` | `FK -> issues.id` | NULLABLE, INDEX, SET NULL | 연관 이슈 |
| `article_id` | `FK -> raw_articles.id` | NOT NULL, INDEX, CASCADE | 원본 기사 |
| `update_type` | `Enum(UpdateType)` | NOT NULL | NEW / MINOR_UPDATE / MAJOR_UPDATE / DUP |
| `update_score` | `Float` | NOT NULL, default=0.0 | 분류 점수 |
| `major_reasons` | `JSON` | NULLABLE | 주요 변경 사유 |
| `diff_summary` | `Text` | NULLABLE | 변경 요약 |
| `duplicate_of_id` | `String(36)` | NULLABLE | 중복 대상 기사 ID |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**인덱스**: `ix_eu_issue_created` (issue_id, created_at)

#### LiveFeedItem -- `live_feed_items`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `issue_id` | `FK -> issues.id` | NULLABLE, INDEX, SET NULL | 연관 이슈 |
| `update_id` | `FK -> event_updates.id` | NOT NULL, INDEX, CASCADE | 기사 업데이트 |
| `feed_type` | `Enum(FeedType)` | NOT NULL | breaking / major / all |
| `rank_score` | `Float` | NOT NULL, default=0.0 | 랭킹 점수 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**인덱스**: `ix_lfi_feed_rank_created` (feed_type, rank_score, created_at)

#### CrawledKeyword -- `crawled_keywords`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `keyword` | `String(100)` | NOT NULL, INDEX | 키워드 |
| `count` | `Integer` | NOT NULL | 출현 횟수 |
| `rank` | `Integer` | NOT NULL | 채널 내 순위 |
| `channel_code` | `String(20)` | NULLABLE, INDEX | 채널 코드 |
| `channel_name` | `String(50)` | NULLABLE | 채널명 |
| `category` | `String(20)` | NULLABLE | 분류 |
| `source_type` | `String(20)` | NOT NULL, INDEX | 소스 유형 |
| `crawled_at` | `DateTime(tz)` | NOT NULL, INDEX | 수집 시각 |
| `created_at` | `DateTime(tz)` | NOT NULL | DB 저장 시각 |

#### KeywordIntersection -- `keyword_intersections`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `keyword` | `String(100)` | NOT NULL, INDEX | 키워드 |
| `channel_count` | `Integer` | NOT NULL, INDEX | 교차 채널 수 |
| `total_count` | `Integer` | NOT NULL | 총 출현 횟수 |
| `channel_codes` | `Text` | NOT NULL | 채널 코드 목록 |
| `rank` | `Integer` | NOT NULL | 교집합 순위 |
| `min_channels` | `Integer` | NOT NULL | 최소 채널 수 기준 |
| `crawled_at` | `DateTime(tz)` | NOT NULL, INDEX | 수집 시각 |
| `created_at` | `DateTime(tz)` | NOT NULL | DB 저장 시각 |

#### IssueKeywordState -- `issue_keyword_states`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `issue_id` | `FK -> issues.id` | NOT NULL, INDEX, CASCADE | 소속 이슈 |
| `normalized_keyword` | `String(200)` | NOT NULL | 정규화 키워드 |
| `status` | `Enum(KeywordLinkStatus)` | NOT NULL, default=ACTIVE | active / cooldown / closed |
| `last_seen_at` | `DateTime(tz)` | NOT NULL | 마지막 감지 시각 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**인덱스**: `ix_iks_keyword_status_seen` (normalized_keyword, status, last_seen_at)

#### NewsSummaryBatch -- `news_summary_batches`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `provider` | `String(30)` | NOT NULL | openai / gemini / ollama |
| `model` | `String(60)` | NOT NULL | 모델명 |
| `total_keywords` | `Integer` | NOT NULL, default=0 | 키워드 수 |
| `total_articles` | `Integer` | NOT NULL, default=0 | 기사 수 |
| `prompt_tokens` | `Integer` | NOT NULL, default=0 | 프롬프트 토큰 |
| `completion_tokens` | `Integer` | NOT NULL, default=0 | 생성 토큰 |
| `summarized_at` | `DateTime(tz)` | NOT NULL, INDEX | 요약 시각 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**관계**: `summaries: list[NewsKeywordSummary]` (cascade="all, delete-orphan")

#### NewsKeywordSummary -- `news_keyword_summaries`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `batch_id` | `FK -> news_summary_batches.id` | NOT NULL, INDEX, CASCADE | 배치 |
| `keyword` | `String(100)` | NOT NULL, INDEX | 키워드 |
| `summary` | `Text` | NOT NULL | 요약 텍스트 |
| `key_points` | `JSON` | NULLABLE | 핵심 포인트 리스트 |
| `sentiment` | `String(20)` | NOT NULL, default="neutral" | 감성 분석 |
| `category` | `String(30)` | NOT NULL, default="society" | 카테고리 |
| `article_count` | `Integer` | NOT NULL, default=0 | 기사 수 |
| `articles` | `JSON` | NULLABLE | 기사 목록 [{title, url, ...}] |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**인덱스**: `ix_nks_keyword_created`, `ix_nks_category`, `ix_nks_sentiment`

#### NewsSummaryTag -- `news_summary_tags`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `summary_id` | `FK -> news_keyword_summaries.id` | NOT NULL, CASCADE | 소속 요약 |
| `tag` | `String(50)` | NOT NULL, INDEX | 태그명 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**인덱스**: `ix_nst_summary_tag` (summary_id, tag, UNIQUE)

#### NewsChannel -- `news_channels`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `code` | `String(20)` | NOT NULL, UNIQUE, INDEX | 채널 코드 |
| `symbol` | `String(10)` | NOT NULL, UNIQUE, INDEX | 채널 심볼 |
| `name` | `String(50)` | NOT NULL | 채널명 |
| `url` | `String(500)` | NOT NULL | URL |
| `category` | `String(20)` | NOT NULL, INDEX | broadcast / newspaper / online |
| `is_active` | `Boolean` | NOT NULL, default=True, INDEX | 활성 상태 |
| `description` | `Text` | NULLABLE | 설명 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |
| `updated_at` | `DateTime(tz)` | NOT NULL | 수정 일시 |

#### NaverNewsArticle -- `naver_news_articles`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `keyword` | `String(100)` | NOT NULL, INDEX | 검색 키워드 |
| `title` | `String(300)` | NOT NULL | 기사 제목 |
| `original_link` | `String(1000)` | NOT NULL | 원본 링크 |
| `naver_link` | `String(1000)` | NOT NULL | 네이버 링크 |
| `description` | `Text` | NULLABLE | 요약 |
| `pub_date` | `String(40)` | NULLABLE | 발행일 |
| `display_order` | `Integer` | NOT NULL, default=0 | 표시 순서 |
| `raw_data` | `Text` | NULLABLE | 원본 JSON |
| `fetched_at` | `DateTime(tz)` | NOT NULL, INDEX | 수집 일시 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**인덱스**: `ix_nna_keyword_pub` (keyword, pub_date)

#### ProductInfo -- `product_info`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `good_id` | `String(20)` | NOT NULL, UNIQUE, INDEX | 한국소비자원 goodId |
| `good_name` | `String(70)` | NOT NULL | 상품명 |
| `good_unit_div_code` | `String(10)` | NULLABLE | 단위 구분 코드 |
| `good_base_cnt` | `String(10)` | NULLABLE | 기본 수량 |
| `good_smlcls_code` | `String(20)` | NULLABLE | 소분류 코드 |
| `detail_mean` | `String(200)` | NULLABLE | 상세 설명 |
| `good_total_cnt` | `String(15)` | NULLABLE | 총 수량 |
| `good_total_div_code` | `String(10)` | NULLABLE | 총 구분 코드 |
| `product_entp_code` | `String(70)` | NULLABLE | 제조사 코드 |
| `raw_data` | `Text` | NULLABLE | 원본 JSON |
| `fetched_at` | `DateTime(tz)` | NOT NULL, INDEX | 수집 일시 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

**관계**: `prices: list[ProductPrice]` (cascade="all, delete-orphan")

#### ProductPrice -- `product_prices`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `good_id` | `FK -> product_info.good_id` | NOT NULL, INDEX, CASCADE | 상품 ID |
| `price` | `Integer` | NOT NULL | 판매 가격 (원) |
| `store_name` | `String(100)` | NULLABLE | 판매 업소명 |
| `on_sale` | `Boolean` | NOT NULL, default=False | 세일 여부 |
| `survey_date` | `String(10)` | NULLABLE, INDEX | 조사일 |
| `raw_data` | `Text` | NULLABLE | 원본 JSON |
| `fetched_at` | `DateTime(tz)` | NOT NULL, INDEX | 수집 일시 |
| `created_at` | `DateTime(tz)` | NOT NULL | 생성 일시 |

#### JobRun -- `job_runs`

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| `id` | `String(36)` | PK | UUID |
| `job_name` | `String(100)` | NOT NULL, INDEX | 잡 이름 |
| `status` | `String(20)` | NOT NULL | success / failed |
| `detail` | `Text` | NULLABLE | 실행 상세 |
| `started_at` | `DateTime(tz)` | NOT NULL | 시작 시각 |
| `finished_at` | `DateTime(tz)` | NULLABLE | 종료 시각 |

### 3.5 Enum 정의

| Enum | 값 | 용도 |
|------|-----|------|
| `UserRole` | guest, member, admin | 사용자 역할 |
| `SocialProvider` | kakao, naver, google | SNS 제공자 |
| `TagType` | category, region | 태그 유형 |
| `Importance` | low, medium, high | 사건 중요도 |
| `VerificationStatus` | verified, unverified | 검증 상태 |
| `IssueStatus` | ongoing, closed, reignited, unverified | 이슈 상태 |
| `TriggerType` | article, ruling, announcement, correction, status_change | 트리거 유형 |
| `VoteType` | like, dislike | 투표 유형 |
| `SourceEntityType` | event, issue, trigger | 출처 엔티티 유형 |
| `NewsChannelCategory` | broadcast, newspaper, online | 뉴스 채널 분류 |
| `UpdateType` | NEW, MINOR_UPDATE, MAJOR_UPDATE, DUP | 기사 분류 결과 |
| `KeywordLinkStatus` | active, cooldown, closed | 키워드-이슈 연결 상태 |
| `FeedType` | breaking, major, all | 피드 유형 |

### 3.6 ER 관계 다이어그램

```
users ──< user_social_accounts
  |
  ├──< refresh_tokens
  ├──< posts ──< comments ──< comment_likes
  |     |          |
  |     ├──< post_votes
  |     └──>< post_tags >──> tags
  |
  ├──>< user_saved_events >──> events ──>< event_tags >──> tags
  |                              |
  └──>< user_tracked_issues >── issues ──>< issue_tags >──> tags
                                  |    |
                                  |    └──>< issue_events >──> events
                                  |
                                  ├──< triggers
                                  ├──< issue_keyword_states
                                  ├──< event_updates ──< live_feed_items
                                  └──  (event_updates -> raw_articles)

sources ── (polymorphic: entity_type + entity_id -> events|issues|triggers)

search_rankings (독립)
search_histories (독립)

news_summary_batches ──< news_keyword_summaries ──< news_summary_tags
crawled_keywords (독립)
keyword_intersections (독립)
news_channels (독립)
naver_news_articles (독립)
product_info ──< product_prices
job_runs (독립)
```

---

## 4. API 엔드포인트 전체 명세

### 4.1 응답 형식

**성공 응답**:
```json
{
  "success": true,
  "data": { ... },
  "message": "조회 성공",
  "timestamp": "2026-03-09T12:00:00.000Z"
}
```

**에러 응답**:
```json
{
  "success": false,
  "error": {
    "code": "E_RESOURCE_001",
    "message": "사건을 찾을 수 없습니다.",
    "details": {}
  },
  "timestamp": "2026-03-09T12:00:00.000Z"
}
```

### 4.2 페이지네이션 전략

| 전략 | 적용 라우터 | 응답 형태 |
|------|------------|----------|
| 커서 기반 | events, community (posts/comments), feed | `{ items, cursor: { next, hasMore } }` |
| 페이지 기반 | issues, sources, tracking, search | `{ items, pagination: { currentPage, totalPages, totalItems, itemsPerPage, hasNext, hasPrev } }` |

커서는 offset의 base64 인코딩: `encode_cursor(offset) -> base64url(str(offset))`

### 4.3 인증 (auth) -- 7개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 | 상태 코드 |
|---------|--------|------|------|------|----------|
| S-API-AUTH-1 | `POST` | `/api/v1/auth/register` | 회원가입 (이메일+비밀번호). 사용자 정보 + 토큰 반환 | 불필요 | 201 |
| S-API-AUTH-2 | `POST` | `/api/v1/auth/login` | 로그인. 사용자 정보 + accessToken/refreshToken 반환 | 불필요 | 200 |
| S-API-AUTH-3 | `POST` | `/api/v1/auth/refresh` | 리프레시 토큰으로 새 액세스 토큰 발급 | 불필요 | 200 |
| S-API-AUTH-4 | `POST` | `/api/v1/auth/logout` | 로그아웃 (리프레시 토큰 폐기) | member | 200 |
| S-API-AUTH-5 | `GET` | `/api/v1/auth/social/providers` | SNS 로그인 제공자 목록 (["kakao","naver","google"]) | 불필요 | 200 |
| S-API-AUTH-6 | `POST` | `/api/v1/auth/social-login` | SNS OAuth 로그인. 미가입 시 자동 회원가입 | 불필요 | 200 |
| S-API-AUTH-7 | `DELETE` | `/api/v1/auth/withdraw` | 회원탈퇴 (soft delete, `withdrawn_at` 기록) | member | 200 |

**요청/응답 스키마**:

- `RegisterRequest`: `nickname: str`, `email: str`, `password: str`
- `LoginRequest`: `email: str`, `password: str`
- `RefreshRequest`: `refreshToken: str`
- `SocialLoginRequest`: `provider: str`, `code: str`, `redirectUri: str`
- `WithdrawRequest`: `password: str | None`

### 4.4 사용자 (users/me) -- 7개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-USER-1 | `GET` | `/api/v1/users/me` | 내 정보 조회 (프로필, 역할, 가입일) | member |
| S-API-USER-2 | `PATCH` | `/api/v1/users/me` | 내 정보 수정 (닉네임, 프로필 이미지) | member |
| S-API-USER-3 | `POST` | `/api/v1/users/me/change-password` | 비밀번호 변경 (현재 비밀번호 확인 필요) | member |
| S-API-USER-4 | `POST` | `/api/v1/users/me/social-connect` | SNS 계정 연동 **(미구현)** | member |
| S-API-USER-5 | `DELETE` | `/api/v1/users/me/social-disconnect` | SNS 계정 연동 해제 **(미구현)** | member |
| S-API-USER-6 | `GET` | `/api/v1/users/me/activity` | 내 활동 내역 **(미구현, 빈 배열 반환)** | member |
| S-API-USER-7 | `GET` | `/api/v1/users/{id}` | 사용자 공개 프로필 (닉네임, 이미지, 활동 통계) | 불필요 |

### 4.5 사건 (events) -- 7개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-EVENT-1 | `GET` | `/api/v1/events` | 사건 목록 (커서 기반). 필터: importance, startDate, endDate. 정렬: occurredAt, createdAt | 불필요 |
| S-API-EVENT-2 | `GET` | `/api/v1/events/{id}` | 사건 상세 (태그, 출처 포함) | 불필요 |
| S-API-EVENT-3 | `POST` | `/api/v1/events/{id}/save` | 사건 저장 (북마크) | member |
| S-API-EVENT-4 | `DELETE` | `/api/v1/events/{id}/save` | 사건 저장 해제 | member |
| S-API-EVENT-5 | `POST` | `/api/v1/events` | 사건 생성 (tagIds, sourceIds 포함) | admin ¹ |
| S-API-EVENT-6 | `PATCH` | `/api/v1/events/{id}` | 사건 수정 (부분 업데이트) | admin ¹ |
| S-API-EVENT-7 | `DELETE` | `/api/v1/events/{id}` | 사건 삭제 | admin ¹ |

> ¹ 어드민 작업은 `trend-korea-admin`에서 직접 DB 접근으로 처리. 이 API는 하위 호환용으로 유지.

**쿼리 파라미터 (목록)**:
- `cursor: str | None` -- 다음 페이지 커서
- `limit: int` (1~100, default=10) -- 페이지 크기
- `importance: str | None` (low/medium/high) -- 중요도 필터
- `startDate: datetime | None` -- 시작 날짜
- `endDate: datetime | None` -- 종료 날짜
- `sortBy: str` (default="occurredAt") -- 정렬 기준
- `order: str` (asc/desc, default="desc") -- 정렬 방향

### 4.6 이슈 (issues) -- 10개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-ISSUE-1 | `GET` | `/api/v1/issues` | 이슈 목록 (페이지 기반). 필터: status, startDate, endDate | 불필요 |
| S-API-ISSUE-2 | `GET` | `/api/v1/issues/{id}` | 이슈 상세 (태그, 출처, 트리거 포함) | 불필요 |
| S-API-ISSUE-3 | `POST` | `/api/v1/issues` | 이슈 생성 (tagIds, sourceIds, relatedEventIds 포함) | admin ² |
| S-API-ISSUE-4 | `PATCH` | `/api/v1/issues/{id}` | 이슈 수정 | admin ² |
| S-API-ISSUE-5 | `DELETE` | `/api/v1/issues/{id}` | 이슈 삭제 | admin ² |
| S-API-ISSUE-6 | `GET` | `/api/v1/issues/{id}/triggers` | 이슈 트리거 목록 (최대 100건) | 불필요 |
| S-API-ISSUE-7 | `POST` | `/api/v1/issues/{id}/triggers` | 트리거 생성 (sourceIds 포함) | admin ² |
| S-API-ISSUE-8 | `POST` | `/api/v1/issues/{id}/track` | 이슈 추적 등록 | member |
| S-API-ISSUE-9 | `DELETE` | `/api/v1/issues/{id}/track` | 이슈 추적 해제 | member |
| S-API-ISSUE-10 | `GET` | `/api/v1/issues/{id}/timeline` | 이슈 뉴스 업데이트 타임라인 (커서 기반) | 불필요 |

> ² 어드민 작업은 `trend-korea-admin`에서 직접 DB 접근으로 처리. 이 API는 하위 호환용으로 유지.

### 4.7 트리거 (triggers) -- 2개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-TRIGGER-1 | `PATCH` | `/api/v1/triggers/{id}` | 트리거 수정 (summary, type, occurredAt) | admin ³ |
| S-API-TRIGGER-2 | `DELETE` | `/api/v1/triggers/{id}` | 트리거 삭제 (이슈의 latest_trigger_at 자동 갱신) | admin ³ |

> ³ 어드민 작업은 `trend-korea-admin`에서 직접 DB 접근으로 처리. 이 API는 하위 호환용으로 유지.

### 4.8 커뮤니티 (posts/comments) -- 12개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-POST-1 | `GET` | `/api/v1/posts` | 게시글 목록 (커서 기반). tab: latest/popular. 정렬: createdAt | 불필요 |
| S-API-POST-2 | `POST` | `/api/v1/posts` | 게시글 작성 (tagIds 최대 3개, isAnonymous) | member |
| S-API-POST-3 | `GET` | `/api/v1/posts/{id}` | 게시글 상세 (작성자, 태그, 추천 수, 댓글 수) | 불필요 |
| S-API-POST-4 | `PATCH` | `/api/v1/posts/{id}` | 게시글 수정 (본인 또는 admin) | member |
| S-API-POST-5 | `DELETE` | `/api/v1/posts/{id}` | 게시글 삭제 (본인 또는 admin) | member |
| S-API-POST-6 | `GET` | `/api/v1/posts/{id}/comments` | 댓글 목록 (커서 기반, 대댓글 parentId 구분) | 불필요 |
| S-API-POST-7 | `POST` | `/api/v1/posts/{id}/comments` | 댓글 작성 (parentId 지정 시 대댓글) | member |
| S-API-POST-8 | `POST` | `/api/v1/posts/{id}/like` | 게시글 추천/비추천 (type: like/dislike) | member |
| S-API-COMMENT-1 | `PATCH` | `/api/v1/comments/{id}` | 댓글 수정 (본인 또는 admin) | member |
| S-API-COMMENT-2 | `DELETE` | `/api/v1/comments/{id}` | 댓글 삭제 (본인 또는 admin) | member |
| S-API-COMMENT-3 | `POST` | `/api/v1/comments/{id}/like` | 댓글 좋아요 | member |
| S-API-COMMENT-4 | `DELETE` | `/api/v1/comments/{id}/like` | 댓글 좋아요 취소 | member |

### 4.9 검색 (search) -- 4개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-SEARCH-1 | `GET` | `/api/v1/search` | 통합 검색 (페이지 기반). tab: all/events/issues/community | 불필요 |
| S-API-SEARCH-2 | `GET` | `/api/v1/search/events` | 사건 검색 | 불필요 |
| S-API-SEARCH-3 | `GET` | `/api/v1/search/issues` | 이슈 검색 | 불필요 |
| S-API-SEARCH-4 | `GET` | `/api/v1/search/posts` | 게시글 검색 | 불필요 |

**공통 쿼리 파라미터**:
- `q: str` (min_length=1) -- 검색어
- `page: int` (default=1) -- 페이지
- `limit: int` (1~100, default=10) -- 페이지 크기
- `sortBy: str` (default="relevance") -- 정렬 기준

### 4.10 추적 (tracking) -- 2개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-TRACK-1 | `GET` | `/api/v1/users/me/tracked-issues` | 추적 중인 이슈 목록 (페이지 기반). 정렬: trackedAt, latestTriggerAt | member |
| S-API-TRACK-2 | `GET` | `/api/v1/users/me/saved-events` | 저장한 사건 목록 (페이지 기반). 정렬: savedAt, occurredAt | member |

### 4.11 홈 (home) -- 7개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-HOME-1 | `GET` | `/api/v1/home/breaking-news` | 속보 사건 목록 (limit: 1~20, default=10) | 불필요 |
| S-API-HOME-2 | `GET` | `/api/v1/home/hot-posts` | 인기 게시글 (limit: 1~20, default=5, period: 24h) | 불필요 |
| S-API-HOME-3 | `GET` | `/api/v1/home/search-rankings` | 검색어 랭킹 (limit: 1~20, default=10, period: daily/weekly) | 불필요 |
| S-API-HOME-4 | `GET` | `/api/v1/home/trending` | 트렌딩 이슈 (limit: 1~20, default=10, period: 24h) | 불필요 |
| S-API-HOME-5 | `GET` | `/api/v1/home/timeline-minimap` | 타임라인 미니맵 (days: 1~30, default=7) | 불필요 |
| S-API-HOME-6 | `GET` | `/api/v1/home/featured-news` | 주요 뉴스 (limit: 1~20, default=5) | 불필요 |
| S-API-HOME-7 | `GET` | `/api/v1/home/community-media` | 커뮤니티 미디어 (limit: 1~20, default=6) | 불필요 |

### 4.12 태그 (tags) -- 4개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-TAG-1 | `GET` | `/api/v1/tags` | 태그 목록. 필터: type (all/category/region), search | 불필요 |
| S-API-TAG-2 | `POST` | `/api/v1/tags` | 태그 생성 (name, type, slug) | admin ⁴ |
| S-API-TAG-3 | `PATCH` | `/api/v1/tags/{id}` | 태그 수정 (name, slug) | admin ⁴ |
| S-API-TAG-4 | `DELETE` | `/api/v1/tags/{id}` | 태그 삭제 | admin ⁴ |

> ⁴ 어드민 작업은 `trend-korea-admin`에서 직접 DB 접근으로 처리. 이 API는 하위 호환용으로 유지.

### 4.13 출처 (sources) -- 3개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-SOURCE-1 | `GET` | `/api/v1/sources` | 출처 목록 (페이지 기반). 필터: publisher | 불필요 |
| S-API-SOURCE-2 | `POST` | `/api/v1/sources` | 출처 등록 (url, title, publisher, publishedAt) | admin ⁵ |
| S-API-SOURCE-3 | `DELETE` | `/api/v1/sources/{id}` | 출처 삭제 | admin ⁵ |

> ⁵ 어드민 작업은 `trend-korea-admin`에서 직접 DB 접근으로 처리. 이 API는 하위 호환용으로 유지.

### 4.14 피드 (feed) -- 1개 엔드포인트

| Spec ID | 메서드 | 경로 | 설명 | 인증 |
|---------|--------|------|------|------|
| S-API-FEED-1 | `GET` | `/api/v1/feed/live` | 실시간 피드 (커서 기반). type: breaking/major/all | 불필요 |

### 4.15 엔드포인트 합계: 66개

| 라우트 그룹 | 엔드포인트 수 |
|-------------|-------------|
| auth | 7 |
| users/me | 6 |
| users | 1 |
| events | 7 |
| issues | 10 |
| triggers | 2 |
| posts/comments | 12 |
| search | 4 |
| tracking | 2 |
| home | 7 |
| tags | 4 |
| sources | 3 |
| feed | 1 |
| **합계** | **66** |

---

## 5. 인증/인가 시스템

### 5.1 JWT 구조

**Access Token**:
```json
{
  "sub": "<user_id>",
  "role": "member",
  "typ": "access",
  "exp": 1741500000,
  "iat": 1741496400
}
```
- 알고리즘: HS256
- 만료: 60분 (`access_token_expire_minutes`)
- 서명 키: `jwt_secret_key` (환경변수)

**Refresh Token**:
```json
{
  "sub": "<user_id>",
  "typ": "refresh",
  "jti": "<uuid>",
  "exp": 1742706000,
  "iat": 1741496400
}
```
- 만료: 14일 (`refresh_token_expire_days`)
- DB 저장: `refresh_tokens` 테이블에 `token_hash` (SHA-256)와 `jti` 저장
- 폐기: 로그아웃 시 `revoked_at` 기록

### 5.2 비밀번호 보안

- 해싱: `bcrypt.hashpw()` (자동 salt 생성)
- 검증: `bcrypt.checkpw()`
- Refresh Token 해싱: `hashlib.sha256()`

### 5.3 SNS OAuth

지원 제공자: 카카오(`kakao`), 네이버(`naver`), 구글(`google`)

**현재 구현 (간소화)**:
- `/auth/social-login` 호출 시 provider + code 기반으로 가상 이메일 생성
- 미가입 사용자는 자동 회원가입 후 토큰 발급
- 실제 OAuth 토큰 교환은 미구현 (Phase 2)

### 5.4 권한 매트릭스

| 기능 | guest (비로그인) | member | admin |
|------|----------------|--------|-------|
| 사건/이슈/커뮤니티 조회 | O | O | O |
| 검색 | O | O | O |
| 홈 데이터 조회 | O | O | O |
| 사건 저장 / 이슈 추적 | X | O | O |
| 게시글/댓글 작성 | X | O | O |
| 추천/비추천/좋아요 | X | O | O |
| 본인 게시글/댓글 수정/삭제 | X | O | O |
| 사건/이슈/트리거 CRUD | X | X | O * |
| 태그/출처 CRUD | X | X | O * |
| 타인 게시글/댓글 삭제 | X | X | O |

> \* admin 작업은 주로 `trend-korea-admin`에서 수행. 이 API의 admin 엔드포인트는 하위 호환용으로 유지.

### 5.5 CORS 설정

- `cors_origins` 환경변수로 허용 도메인 설정 (쉼표 구분)
- 기본값: `*` (개발 환경)

---

## 6. 데이터 수집 파이프라인

### 6.1 전체 파이프라인 흐름

```
키워드 수집 → 뉴스 크롤링 → (네이버 뉴스) → 기사 분류/중복 제거 → 뉴스 요약 → 피드 저장
```

**진입점**: `src/utils/pipeline/orchestrator.py:run_cycle()`

### 6.2 단계별 상세

#### 단계 1: 키워드 수집

- **모듈**: `src/utils/keyword_crawler/`
- **CLI**: `trend-korea-crawl-keywords --top-n 30 --save-db`
- **동작**: 주요 뉴스 사이트 헤드라인에서 키워드를 추출하고 빈도/교집합 분석
- **출력**: `CrawlOutput` (aggregated_keywords, intersection_keywords)
- **DB 저장**: `crawled_keywords`, `keyword_intersections`
- **키워드 선택 전략**:
  - `intersection`: 교집합 키워드 우선, 부족하면 빈도순 보충
  - `aggregated`: 빈도 기반 상위 키워드만 사용

#### 단계 2: 뉴스 크롤링

- **모듈**: `src/utils/news_crawler/`
- **CLI**: `trend-korea-crawl-news --keyword "키워드" --limit 3`
- **동작**: 선별된 키워드로 뉴스 기사 수집
- **출력**: 기사 리스트 (title, url, content 등)
- **DB 저장**: `raw_articles` (URL 정규화 + 해시 기반 중복 제거)

#### 단계 3: 네이버 뉴스 검색 (선택)

- **모듈**: `src/utils/naver_news_crawler/`
- **CLI**: `trend-korea-crawl-naver-news "키워드1" "키워드2" --display 10 --save-db`
- **동작**: 네이버 뉴스 검색 API로 추가 기사 수집
- **외부 연동**: 네이버 검색 API (`naver_api_client`, `naver_api_client_secret`)
- **DB 저장**: `naver_news_articles`
- **활성화 조건**: `naver_api_client` 환경변수가 설정된 경우

#### 단계 4: 기사 분류/중복 제거

- **모듈**: `src/utils/pipeline/update_classifier.py`
- **동작**: 수집된 기사를 기존 기사와 비교하여 분류
- **분류 결과**: `UpdateType` (NEW / MINOR_UPDATE / MAJOR_UPDATE / DUP)
- **분류 기준 가중치** (설정 가능):
  - keyword: 0.15
  - entity: 0.20
  - semantic: 0.35
  - time: 0.20
  - source: 0.10
- **임계값**:
  - NEW: score < `classifier_score_new` (0.45)
  - MAJOR_UPDATE: score >= `classifier_score_major` (0.70)
  - DUP: 완전 일치 (URL/해시 기반)
- **DB 저장**: `event_updates`

#### 단계 5: 뉴스 요약

- **모듈**: `src/utils/news_summarizer/`
- **CLI**: `trend-korea-summarize-news --input news.json --model gemma3:4b`
- **동작**: DUP 제외 기사를 LLM으로 키워드별 요약
- **외부 연동**: OpenAI API 호환 (Ollama 로컬 / OpenAI / Gemini)
- **기본 모델**: `gemma3:4b` (Ollama)
- **DB 저장**: `news_summary_batches`, `news_keyword_summaries`, `news_summary_tags`
- **토큰 추적**: prompt_tokens, completion_tokens 기록

#### 단계 6: 피드 저장

- **모듈**: `src/utils/pipeline/feed_builder.py`
- **동작**: 분류 결과를 피드 항목으로 변환
- **피드 유형 결정**:
  - `breaking`: update_score >= `feed_breaking_score_threshold` (0.85)
  - `major`: MAJOR_UPDATE (boost: `feed_major_boost` = 1.5)
  - `all`: 나머지
- **DB 저장**: `live_feed_items`

### 6.3 전체 파이프라인 CLI

```bash
trend-korea-full-cycle --repeat 1 --max-keywords 3 --top-n 30 --limit 3
```

**파라미터**:

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `--repeat` | 10 | 반복 횟수 |
| `--top-n` | 30 | 수집할 상위 키워드 수 |
| `--max-keywords` | 5 | 크롤링에 사용할 최대 키워드 수 |
| `--limit` | 3 | 키워드당 최대 기사 수 |
| `--model` | gemma3:4b | LLM 모델 |
| `--use-naver` | True | 네이버 뉴스 사용 여부 |
| `--keyword-strategy` | intersection | 키워드 선택 전략 |
| `--enable-classification` | True | 분류 활성화 여부 |

### 6.4 생필품 가격 크롤러

- **모듈**: `src/utils/product_crawler/`
- **CLI**: `trend-korea-crawl-products --max-pages 2 --save-db`
- **외부 연동**: 한국소비자원 API (`openapi_product_price_encoding_key`, `openapi_product_price_decoding_key`)
- **DB 저장**: `product_info`, `product_prices`
- **상태**: Phase 2 (별도 스케줄러 잡 미등록)

---

## 7. 스케줄러 잡

### 7.1 워커 프로세스

**진입점**: `src/worker_main.py:run()` (`trend-korea-worker`)

APScheduler `BlockingScheduler`로 별도 프로세스에서 실행. 타임존: `Asia/Seoul`.

### 7.2 잡 목록 (6개)

| 잡 이름 | 주기 | 트리거 | 설명 | Spec ID |
|---------|------|--------|------|---------|
| `news_collect` | 15분 간격 | interval | 뉴스 수집 전체 파이프라인 1사이클 | S-JOB-1 |
| `keyword_state_cleanup` | 60분 간격 | interval | 이슈-키워드 상태 전환 | S-JOB-2 |
| `issue_status_reconcile` | 30분 (*/30) | cron | 이슈 상태 자동 보정 | S-JOB-3 |
| `search_rankings` | 매시 정각 | cron | 검색 랭킹 재계산 | S-JOB-4 |
| `community_hot_score` | 10분 (*/10) | cron | 커뮤니티 인기 점수 갱신 | S-JOB-5 |
| `cleanup_refresh_tokens` | 매일 03:00 | cron | 만료/폐기된 리프레시 토큰 삭제 | S-JOB-6 |

### 7.3 잡 상세

#### S-JOB-1: news_collect

- **핸들러**: `run_news_collect_cycle(db)`
- **로직**: `run_cycle()` 호출 (키워드 30개 수집 -> 5개 선별 -> 기사 크롤링 -> 분류 -> 요약)
- **출력**: `cycle_outputs/scheduled_{timestamp}/` 디렉토리에 결과 저장
- **설정**: `schedule_news_collect_minutes` (환경변수)

#### S-JOB-2: keyword_state_cleanup

- **핸들러**: `cleanup_keyword_states(db)`
- **로직**:
  - `last_seen_at` 48시간 경과: ACTIVE -> COOLDOWN
  - `last_seen_at` 120시간(48+72) 경과: COOLDOWN -> CLOSED
- **설정**: `schedule_keyword_cleanup_minutes` (환경변수)

#### S-JOB-3: issue_status_reconcile

- **핸들러**: `reconcile_issue_status(db)`
- **로직**:
  - `latest_trigger_at`이 30일 경과한 ONGOING -> CLOSED
  - `latest_trigger_at`이 7일 이내인 CLOSED -> REIGNITED

#### S-JOB-4: search_rankings

- **핸들러**: `recalculate_search_rankings(db)`
- **로직**:
  - 최근 24시간 사건/이슈/게시글 제목에서 토큰 추출
  - 빈도 기반 상위 10개 키워드 선정
  - 7일 이상 지난 랭킹 삭제
  - `search_rankings` 테이블에 새 랭킹 저장

#### S-JOB-5: community_hot_score

- **핸들러**: `recalculate_community_hot_score(db)`
- **로직**: 모든 게시글의 `comment_count`를 실제 댓글 수와 동기화

#### S-JOB-6: cleanup_refresh_tokens

- **핸들러**: `cleanup_refresh_tokens(db)`
- **로직**: 만료된 토큰 + 30일 이상 폐기된 토큰 삭제

### 7.4 잡 실행 추적

모든 잡은 `run_job()` 래퍼를 통해 실행되며, 결과를 `job_runs` 테이블에 기록:

```python
def run_job(job_name: str, handler: Callable[[Session], str | None]) -> None:
    # 1. handler(db) 실행
    # 2. 성공/실패 상태 + detail을 job_runs에 기록
```

---

## 8. 비기능 요구사항

### 8.1 성능

| 지표 | 목표 | 비고 |
|------|------|------|
| API 응답 시간 (P95) | < 500ms | 페이지네이션 적용 |
| DB 쿼리 시간 (P95) | < 100ms | 인덱스 최적화 |
| 동시 접속 | 100+ | uvicorn 워커 설정 |

### 8.2 보안

| 항목 | 대응 |
|------|------|
| SQL Injection | SQLAlchemy 파라미터 바인딩 (`.where()`, `.values()`) |
| 비밀번호 | bcrypt 해싱 (자동 salt) |
| 토큰 보안 | JWT HS256 + Refresh Token DB 해시 저장 + 만료/폐기 관리 |
| CORS | 환경변수 기반 허용 도메인 설정 |
| 권한 체크 | `CurrentMemberUserId` / `CurrentAdminUserId` 의존성 주입 |
| 시크릿 관리 | `.env` 파일 기반, 코드 하드코딩 금지 |

### 8.3 데이터베이스

| 항목 | 상세 |
|------|------|
| 인덱스 | 모든 FK, 검색 대상 필드, 정렬 대상 필드에 INDEX 적용 |
| 마이그레이션 | Alembic (`uv run alembic upgrade head`) |
| Cascade | 모든 FK에 `ondelete="CASCADE"` 또는 `SET NULL` 적용 |
| Unique 제약 | email, nickname, slug, token_hash, jti, canonical_url |
| 복합 인덱스 | event_updates(issue_id, created_at), live_feed_items(feed_type, rank_score, created_at) |

### 8.4 모니터링/로깅

| 항목 | 상세 |
|------|------|
| 잡 실행 이력 | `job_runs` 테이블 (job_name, status, detail, started_at, finished_at) |
| 파이프라인 리포트 | `cycle_outputs/` 디렉토리에 JSON 결과 파일 |
| 헬스체크 | `/health/live` (Liveness), `/health/ready` (Readiness) -- 구현 필요 |

---

## 9. 배포/인프라

### 9.1 환경변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `DATABASE_URL` | O | - | PostgreSQL 연결 문자열 |
| `JWT_SECRET_KEY` | O | "change-me-in-env" | JWT 서명 키 (16자 이상) |
| `APP_ENV` | X | "local" | 환경 (local/staging/production) |
| `APP_HOST` | X | "0.0.0.0" | 바인드 호스트 |
| `APP_PORT` | X | 8000 | 포트 |
| `CORS_ORIGINS` | X | "*" | 허용 도메인 (쉼표 구분) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | X | 60 | 액세스 토큰 만료 시간 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | X | 14 | 리프레시 토큰 만료 일수 |
| `SCHEDULER_TIMEZONE` | X | "Asia/Seoul" | 스케줄러 타임존 |
| `AUTO_CREATE_TABLES` | X | True | 시작 시 테이블 자동 생성 |
| `OLLAMA_BASE_URL` | X | "http://localhost:11434/v1" | Ollama API 기본 URL |
| `OLLAMA_DEFAULT_MODEL` | X | "gemma3:4b" | 기본 LLM 모델 |
| `NAVER_API_CLIENT` | X | "" | 네이버 검색 API 클라이언트 ID |
| `NAVER_API_CLIENT_SECRET` | X | "" | 네이버 검색 API 시크릿 |
| `OPENAPI_PRODUCT_PRICE_ENCODING_KEY` | X | "" | 한국소비자원 API 인코딩 키 |
| `OPENAPI_PRODUCT_PRICE_DECODING_KEY` | X | "" | 한국소비자원 API 디코딩 키 |
| `SCHEDULE_NEWS_COLLECT_MINUTES` | X | 15 | 뉴스 수집 주기 (분) |
| `SCHEDULE_KEYWORD_CLEANUP_MINUTES` | X | 60 | 키워드 정리 주기 (분) |
| `CLASSIFIER_SCORE_NEW` | X | 0.45 | NEW 분류 임계값 |
| `CLASSIFIER_SCORE_MAJOR` | X | 0.70 | MAJOR_UPDATE 분류 임계값 |
| `CLASSIFIER_WEIGHT_KEYWORD` | X | 0.15 | 분류기 키워드 가중치 |
| `CLASSIFIER_WEIGHT_ENTITY` | X | 0.20 | 분류기 엔티티 가중치 |
| `CLASSIFIER_WEIGHT_SEMANTIC` | X | 0.35 | 분류기 시맨틱 가중치 |
| `CLASSIFIER_WEIGHT_TIME` | X | 0.20 | 분류기 시간 가중치 |
| `CLASSIFIER_WEIGHT_SOURCE` | X | 0.10 | 분류기 출처 가중치 |
| `FEED_BREAKING_SCORE_THRESHOLD` | X | 0.85 | 속보 피드 점수 임계값 |
| `FEED_MAJOR_BOOST` | X | 1.5 | MAJOR_UPDATE 피드 점수 부스트 |
| `CLASSIFIER_CANDIDATE_WINDOW_HOURS` | X | 72 | 분류기 후보 기사 검색 시간 범위 (시간) |
| `NEWS_PIPELINE_DIR` | X | "" | 파이프라인 결과 저장 디렉토리 |
| `OPENAPI_PRODUCT_PRICE_ENDPOINT` | X | "http://openapi.price.go.kr/openApiImpl/ProductPriceInfoService" | 한국소비자원 API 엔드포인트 |

### 9.2 진입점

| 명령어 | 진입점 | 설명 |
|--------|--------|------|
| `trend-korea-api` | `src/main.py:run` | API 서버 (uvicorn :8000) |
| `trend-korea-worker` | `src/worker_main.py:run` | 스케줄러 워커 |
| `trend-korea-crawl-keywords` | `src/utils/keyword_crawler/cli.py:main` | 키워드 수집 CLI |
| `trend-korea-crawl-news` | `src/utils/news_crawler/cli.py:main` | 뉴스 크롤링 CLI |
| `trend-korea-crawl-naver-news` | `src/utils/naver_news_crawler/cli.py:main` | 네이버 뉴스 CLI |
| `trend-korea-summarize-news` | `src/utils/news_summarizer/cli.py:main` | 뉴스 요약 CLI |
| `trend-korea-crawl-products` | `src/utils/product_crawler/cli.py:main` | 생필품 크롤러 CLI |
| `trend-korea-full-cycle` | `src/utils/pipeline/cli.py:main` | 전체 파이프라인 CLI |

### 9.3 의존성 그룹

```bash
uv sync                              # 기본 (API + 워커)
uv sync --extra crawler              # + 크롤러 의존성
uv sync --extra summarizer           # + 요약기 의존성
uv sync --extra crawler --extra summarizer  # 전체
```

---

## 10. AI 에이전트 Boundaries

### Always (항상 지킬 것)

- `api -> schemas -> crud -> sql -> models` 레이어 순서 준수
- 새 모델 추가 시 `db/__init__.py`에 배럴 import 등록 필수
- ruff 린트/포맷 통과 (`line-length=100`, `target-version=py311`)
- 타입 힌트 필수 (`X | None` 스타일, `Optional[X]` 사용 금지)
- SQLAlchemy 2.0 `select()` 스타일 (`session.query()` 사용 금지)
- Pydantic V2 문법 (`field_validator`, `model_validator`, `model_config`)
- Import: `from src.{layer}.{domain} import ...`
- ForeignKey는 테이블명 문자열 참조: `ForeignKey("users.id")`
- 응답 형식: `success_response()` / `error_response()` 사용
- 에러 처리: `AppError(code=, message=, status_code=)` 사용
- 테스트: 새 기능은 반드시 `uv run pytest` 통과

### Ask First (먼저 확인할 것)

- DB 스키마 변경 (Alembic 마이그레이션 필요)
- 새 외부 API/서비스 의존성 추가
- 인증/인가 로직 변경
- 스케줄러 잡 주기 변경
- LLM 모델/프롬프트 변경
- 새 라우트 그룹 추가
- 파이프라인 분류기 가중치/임계값 변경

### Never (절대 하지 말 것)

- 프로덕션 DB 직접 접근 또는 데이터 삭제
- `.env`, 시크릿 키, API 키를 코드에 하드코딩
- 보안 미들웨어/인증 체크 우회
- `db/__init__.py` 배럴 import 누락
- `session.query()` 사용 (2.0 스타일만 허용)
- 테스트 없이 비즈니스 로직 변경
- `Optional[X]` 사용 (`X | None`으로 통일)

### Commands

```bash
# 서버
uv run trend-korea-api               # API 서버 (:8000)
uv run trend-korea-worker            # 스케줄러 워커

# 검증
uv run pytest                        # 테스트
uv run pytest tests/test_auth.py -v  # 개별 테스트
uv run pytest --cov=src              # 커버리지
uv run ruff check src/               # 린트
uv run ruff format src/              # 포매팅

# DB
uv run alembic upgrade head          # 마이그레이션 적용
uv run alembic revision --autogenerate -m "설명"  # 마이그레이션 생성

# 파이프라인
uv run trend-korea-full-cycle --repeat 1 --max-keywords 3
uv run trend-korea-crawl-keywords --top-n 30 --save-db
uv run trend-korea-crawl-news --keyword "키워드" --limit 3
uv run trend-korea-crawl-naver-news "키워드" --display 10 --save-db
uv run trend-korea-summarize-news --input news.json --model gemma3:4b
uv run trend-korea-crawl-products --max-pages 2 --save-db
```

---

## 11. MVP 범위 및 로드맵

### 11.1 현재 구현 상태 (Phase 1 -- MVP)

- [x] 인증 시스템 (이메일 가입/로그인/로그아웃/회원탈퇴, JWT, SNS 로그인 간소화)
- [x] 사건 CRUD + 저장/해제 (admin 생성/수정/삭제, member 저장)
- [x] 이슈 CRUD + 추적/해제 + 트리거 관리 (admin CRUD, member 추적)
- [x] 커뮤니티 (게시글 CRUD, 댓글/대댓글, 추천/비추천, 댓글 좋아요)
- [x] 통합 검색 (사건/이슈/게시글 탭별 검색, 페이지 기반)
- [x] 내 추적 (추적 이슈/저장 사건 모아보기, 페이지 기반)
- [x] 사용자 관리 (내 정보 조회/수정, 비밀번호 변경, 공개 프로필)
- [x] 홈 데이터 (속보, 인기 게시글, 검색 랭킹, 트렌딩, 미니맵, 주요 뉴스, 미디어)
- [x] 태그/출처 CRUD (admin 전용)
- [x] 실시간 피드 (live_feed_items 기반)
- [x] 뉴스 수집 파이프라인 (키워드 -> 크롤링 -> 분류 -> 요약 -> 피드)
- [x] 스케줄러 워커 (6개 잡)
- [x] 에러 코드 체계 + 응답 형식 통일
- [x] 커서/페이지 기반 페이지네이션

### 11.2 미구현/미완성

- [ ] SNS 연동 (`/users/me/social-connect`, `/social-disconnect` -- stub 반환)
- [ ] 내 활동 내역 (`/users/me/activity` -- 빈 배열 반환)
- [ ] 실제 OAuth 토큰 교환 (현재 가상 이메일 생성)
- [ ] 헬스체크 엔드포인트 (`/health/live`, `/health/ready`)
- [ ] Rate Limiting (인증 엔드포인트)
- [이관됨] 사용자 관리 API (admin: 역할 변경, 정지/복원) → `trend-korea-admin`으로 이관
- [이관됨] 신고 시스템 (데이터 모델 + API) → `trend-korea-admin`으로 이관
- [ ] 생필품 가격 스케줄러 잡

### 11.3 Phase 2 (개선)

- [ ] 실제 OAuth 토큰 교환 구현 (카카오/네이버/구글)
- [ ] SNS 계정 연동/해제 실제 구현
- [ ] 내 활동 내역 실제 구현
- [이관됨] 사용자 관리 API (admin) → `trend-korea-admin`으로 이관
- [이관됨] 신고 시스템 → `trend-korea-admin`으로 이관
- [ ] 헬스체크 + 모니터링
- [ ] Rate Limiting
- [ ] 이미지 업로드 (S3/R2)
- [ ] WebSocket/SSE 실시간 피드

### 11.4 Phase 3 (확장)

- [ ] 전문 검색 (PostgreSQL FTS / Elasticsearch)
- [ ] 알림 시스템 (푸시/이메일)
- [ ] 오픈 API + API 키 관리
- [ ] 데이터 내보내기 (CSV/JSON)
- [ ] 생필품 가격 스케줄러 잡 + API

---

## 12. 용어 사전

| 한글 | 영문 | 코드 | DB 테이블 | 설명 |
|------|------|------|----------|------|
| 사건 | Event | `Event` | `events` | 특정 일자에 발생한 단일 이벤트 |
| 이슈 | Issue | `Issue` | `issues` | 언론/SNS에서 지속 추적되는 주제 |
| 트리거 | Trigger | `Trigger` | `triggers` | 이슈에 대한 새로운 업데이트 |
| 태그 | Tag | `Tag` | `tags` | 사건/이슈 분류 라벨 (분야/지역) |
| 출처 | Source | `Source` | `sources` | 뉴스 기사, 공식 발표 등 참고 자료 |
| 게시글 | Post | `Post` | `posts` | 커뮤니티 게시글 |
| 댓글 | Comment | `Comment` | `comments` | 게시글에 대한 댓글/대댓글 |
| 사용자 | User | `User` | `users` | 서비스 사용자 |
| 검색순위 | Search Ranking | `SearchRanking` | `search_rankings` | 인기 검색 키워드 순위 |
| 원본 기사 | Raw Article | `RawArticle` | `raw_articles` | 크롤링된 뉴스 기사 |
| 기사 분류 | Event Update | `EventUpdate` | `event_updates` | 기사별 분류 결과 (NEW/MINOR/MAJOR/DUP) |
| 피드 항목 | Live Feed Item | `LiveFeedItem` | `live_feed_items` | 실시간 피드 사전 계산 행 |
| 수집 키워드 | Crawled Keyword | `CrawledKeyword` | `crawled_keywords` | 트렌드 키워드 수집 결과 |
| 키워드 교집합 | Keyword Intersection | `KeywordIntersection` | `keyword_intersections` | 키워드 교차 분석 결과 |
| 키워드 상태 | Issue Keyword State | `IssueKeywordState` | `issue_keyword_states` | 이슈-키워드 연결 상태 |
| 뉴스 요약 | News Summary | `NewsKeywordSummary` | `news_keyword_summaries` | LLM 요약 결과 |
| 잡 실행 | Job Run | `JobRun` | `job_runs` | 스케줄러 잡 실행 이력 |

---

> **완성도**: 코드베이스 실사 기반 백엔드 API 명세 (2026-03-09 기술 검증 반영)
