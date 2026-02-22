# Trend Korea API

대한민국 사회 이슈·사건을 실시간으로 추적·분석하는 플랫폼의 백엔드 API입니다.

- 사건(Event)·이슈(Issue) CRUD 및 추적/저장
- 커뮤니티 게시글·댓글·추천
- 통합 검색 및 검색 랭킹
- 뉴스 키워드 크롤러
- 스케줄러 기반 백그라운드 작업 (이슈 상태 조정, 검색 랭킹 재계산 등)

## 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| 프레임워크 | FastAPI |
| ORM | SQLAlchemy 2.0 (sync) |
| 검증 | Pydantic V2 + pydantic-settings |
| 데이터베이스 | PostgreSQL 16 |
| 마이그레이션 | Alembic |
| 스케줄러 | APScheduler |
| 인증 | JWT (python-jose, bcrypt) |
| 패키지 매니저 | uv |
| 린터 | ruff (line-length=100, py311) |

## 시작하기

### 사전 요구사항

- Python 3.11+
- PostgreSQL 16+
- [uv](https://docs.astral.sh/uv/)

### 설치

```bash
git clone <repository-url>
cd trend-korea-backend
uv sync
```

크롤러 의존성이 필요한 경우:

```bash
uv sync --extra crawler
```

### 환경변수

`.env.example`을 복사하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

| 변수 | 필수 | 기본값 | 설명 |
|------|:----:|--------|------|
| `DATABASE_URL` | O | - | PostgreSQL 연결 문자열 |
| `JWT_SECRET_KEY` | O (운영) | `change-me-in-env` | JWT 서명 키 (16자 이상) |
| `APP_ENV` | | `local` | 실행 환경 (`local`, `dev`, `prod`) |
| `APP_HOST` | | `0.0.0.0` | 서버 호스트 |
| `APP_PORT` | | `8000` | 서버 포트 |
| `CORS_ORIGINS` | | `*` | 허용 오리진 (쉼표 구분) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `60` | 액세스 토큰 만료 시간(분) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | `14` | 리프레시 토큰 만료 시간(일) |
| `JWT_ALGORITHM` | | `HS256` | JWT 알고리즘 |
| `SCHEDULER_TIMEZONE` | | `Asia/Seoul` | 스케줄러 타임존 |
| `AUTO_CREATE_TABLES` | | `true` | 서버 시작 시 테이블 자동 생성 |

### 실행

```bash
# 개발 서버 (auto-reload 활성)
uv run trend-korea-api

# 스케줄러 워커
uv run trend-korea-worker

# 키워드 크롤러
uv run trend-korea-crawl-keywords --help
uv run trend-korea-crawl-keywords --top-n 30 --save-db
```

### Docker

`docker-compose.yml`은 PostgreSQL 컨테이너를 제공합니다.

```bash
docker compose up -d
```

기본 연결 정보: `postgresql://postgres:postgres@localhost:5432/trend_korea`

## 프로젝트 구조

레이어 기반(Layer-based) 아키텍처를 사용합니다. 각 레이어는 도메인별 파일로 구성됩니다.

```
src/
├── main.py                 # FastAPI 앱 진입점
├── worker_main.py          # APScheduler 워커 진입점
├── api/v1/                 # 라우터 (엔드포인트)
│   ├── auth.py
│   ├── users.py
│   ├── events.py
│   ├── issues.py
│   ├── community.py
│   ├── search.py
│   ├── tracking.py
│   ├── home.py
│   ├── tags.py
│   ├── sources.py
│   └── triggers.py
├── models/                 # SQLAlchemy 2.0 모델
├── schemas/                # Pydantic V2 요청/응답 스키마
├── crud/                   # 비즈니스 로직 (서비스)
├── sql/                    # 데이터 액세스 계층 (레포지토리)
├── core/                   # 설정, 보안, 예외, 로깅, 페이지네이션
├── db/                     # Base 모델, 세션, enum, 배럴 import
├── utils/                  # 의존성 주입, 에러 핸들러, 소셜 인증
├── scheduler/              # 스케줄러 잡 정의
└── keyword_crawler/        # 뉴스 키워드 크롤러
```

### 레이어 디렉터리 패턴

각 레이어는 동일한 도메인 파일명으로 대응됩니다:

| 레이어 | 경로 | 역할 |
|--------|------|------|
| 라우터 | `api/v1/{domain}.py` | FastAPI 엔드포인트 |
| 스키마 | `schemas/{domain}.py` | Pydantic V2 요청/응답 |
| 모델 | `models/{domain}.py` | SQLAlchemy ORM 모델 |
| 서비스 | `crud/{domain}.py` | 비즈니스 로직 |
| 저장소 | `sql/{domain}.py` | 데이터 액세스 |

## API 엔드포인트

### 인증 (`/api/v1/auth`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| POST | `/register` | - | 회원가입 |
| POST | `/login` | - | 로그인 |
| POST | `/refresh` | - | 토큰 갱신 |
| POST | `/logout` | Bearer | 로그아웃 |
| GET | `/social/providers` | - | SNS 제공자 목록 |
| POST | `/social-login` | - | SNS 로그인 |
| DELETE | `/withdraw` | Bearer | 회원 탈퇴 |

### 사용자 (`/api/v1/users`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/me` | Bearer | 내 프로필 조회 |
| PATCH | `/me` | Bearer | 프로필 수정 |
| POST | `/me/change-password` | Bearer | 비밀번호 변경 |
| POST | `/me/social-connect` | Bearer | SNS 연동 (스텁) |
| DELETE | `/me/social-disconnect` | Bearer | SNS 연동 해제 (스텁) |
| GET | `/me/activity` | Bearer | 활동 내역 (스텁) |
| GET | `/{user_id}` | - | 공개 프로필 조회 |

### 사건 (`/api/v1/events`) — 커서 기반 페이지네이션

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/` | - | 사건 목록 |
| GET | `/{event_id}` | - | 사건 상세 |
| POST | `/` | Admin | 사건 생성 |
| PATCH | `/{event_id}` | Admin | 사건 수정 |
| DELETE | `/{event_id}` | Admin | 사건 삭제 |
| POST | `/{event_id}/save` | Bearer | 사건 저장 |
| DELETE | `/{event_id}/save` | Bearer | 사건 저장 해제 |

### 이슈 (`/api/v1/issues`) — 페이지 기반 페이지네이션

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/` | - | 이슈 목록 |
| GET | `/{issue_id}` | - | 이슈 상세 |
| POST | `/` | Admin | 이슈 생성 |
| PATCH | `/{issue_id}` | Admin | 이슈 수정 |
| DELETE | `/{issue_id}` | Admin | 이슈 삭제 |
| POST | `/{issue_id}/track` | Bearer | 이슈 추적 |
| DELETE | `/{issue_id}/track` | Bearer | 이슈 추적 해제 |
| GET | `/{issue_id}/triggers` | - | 트리거 목록 |
| POST | `/{issue_id}/triggers` | Admin | 트리거 생성 |

### 트리거 (`/api/v1/triggers`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| PATCH | `/{trigger_id}` | Admin | 트리거 수정 |
| DELETE | `/{trigger_id}` | Admin | 트리거 삭제 |

### 커뮤니티 (`/api/v1/posts`, `/api/v1/comments`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/posts` | - | 게시글 목록 (커서 기반) |
| POST | `/posts` | Bearer | 게시글 작성 (태그 최대 3개) |
| GET | `/posts/{post_id}` | - | 게시글 상세 |
| PATCH | `/posts/{post_id}` | Bearer | 게시글 수정 (작성자/관리자) |
| DELETE | `/posts/{post_id}` | Bearer | 게시글 삭제 (작성자/관리자) |
| GET | `/posts/{post_id}/comments` | - | 댓글 목록 |
| POST | `/posts/{post_id}/comments` | Bearer | 댓글 작성 |
| PATCH | `/comments/{comment_id}` | Bearer | 댓글 수정 |
| DELETE | `/comments/{comment_id}` | Bearer | 댓글 삭제 |
| POST | `/posts/{post_id}/votes` | Bearer | 게시글 추천/비추천 |
| DELETE | `/posts/{post_id}/votes` | Bearer | 추천 취소 |
| POST | `/comments/{comment_id}/likes` | Bearer | 댓글 좋아요 |
| DELETE | `/comments/{comment_id}/likes` | Bearer | 댓글 좋아요 취소 |

### 검색 (`/api/v1/search`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/` | - | 통합 검색 (all/events/issues/community) |
| GET | `/events` | - | 사건 검색 |
| GET | `/issues` | - | 이슈 검색 |
| GET | `/community` | - | 커뮤니티 검색 |

### 트래킹 (`/api/v1/users/me`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/tracked-issues` | Bearer | 추적 중인 이슈 목록 |
| GET | `/saved-events` | Bearer | 저장한 사건 목록 |

### 홈 (`/api/v1/home`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/breaking-news` | - | 속보 피드 |
| GET | `/hot-posts` | - | 인기 게시글 |
| GET | `/search-rankings` | - | 검색 키워드 랭킹 |
| GET | `/trending` | - | 트렌딩 토픽 (스텁) |
| GET | `/timeline` | - | 타임라인 (스텁) |

### 태그 (`/api/v1/tags`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/` | - | 태그 목록 (타입·검색 필터) |
| POST | `/` | Admin | 태그 생성 |
| PATCH | `/{tag_id}` | Admin | 태그 수정 |
| DELETE | `/{tag_id}` | Admin | 태그 삭제 |

### 출처 (`/api/v1/sources`)

| Method | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/` | - | 출처 목록 (페이지 기반) |
| POST | `/` | Admin | 출처 등록 |
| DELETE | `/{source_id}` | Admin | 출처 삭제 |

### 헬스체크

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /health/live` | Liveness 체크 |
| `GET /health/ready` | Readiness 체크 |

## 인증

JWT 기반 인증을 사용합니다.

| 항목 | 값 |
|------|-----|
| 알고리즘 | HS256 |
| Access Token 만료 | 60분 (설정 가능) |
| Refresh Token 만료 | 14일 (설정 가능) |
| SNS 로그인 | 카카오, 네이버, 구글 |

### 권한 레벨

| 레벨 | 대상 | 설명 |
|------|------|------|
| Public | 비인증 | 목록·검색·홈 피드·공개 프로필 조회 |
| Member | Bearer 토큰 | 추적·저장·게시글·댓글·추천 |
| Admin | Bearer + admin 역할 | 사건·이슈·태그·출처·트리거 관리 |

## 응답 형식

### 성공

```json
{
  "success": true,
  "data": { ... },
  "message": "작업 성공",
  "timestamp": "2026-02-22T12:34:56.789Z"
}
```

### 에러

```json
{
  "success": false,
  "error": {
    "code": "E_AUTH_001",
    "message": "유효하지 않은 토큰입니다.",
    "details": { ... }
  },
  "timestamp": "2026-02-22T12:34:56.789Z"
}
```

### 에러 코드 체계

| 접두사 | 분류 | 예시 |
|--------|------|------|
| `E_AUTH_` | 인증 | 잘못된 비밀번호, 토큰 만료/무효 |
| `E_PERM_` | 권한 | 작성자 아님, 관리자 권한 필요 |
| `E_VALID_` | 검증 | 필수 필드 누락, 포맷 오류 |
| `E_RESOURCE_` | 리소스 | 사건·이슈·게시글·댓글·사용자·태그·트리거 미존재 |
| `E_CONFLICT_` | 충돌 | 이메일 중복, 이미 추적/저장 중 |
| `E_SERVER_` | 서버 | 내부 서버 오류 |

## 테스트

```bash
# 전체 테스트 실행
uv run pytest

# 특정 도메인 테스트
uv run pytest tests/test_auth.py -v

# 커버리지 확인
uv run pytest --cov=src
```

테스트는 SQLite in-memory DB를 사용하며, 트랜잭션 롤백으로 테스트 간 데이터를 격리합니다.

| 테스트 파일 | 대상 도메인 |
|------------|-----------|
| `test_auth.py` | 인증 (회원가입, 로그인, 토큰 갱신, 탈퇴) |
| `test_users.py` | 사용자 (프로필, 비밀번호 변경) |
| `test_events.py` | 사건 (목록, 상세, 저장, 관리자 CRUD) |
| `test_issues.py` | 이슈 (목록, 상세, 트래킹, 관리자 CRUD) |
| `test_triggers.py` | 트리거 (관리자 수정/삭제) |
| `test_community_posts.py` | 게시글 (CRUD, 좋아요/싫어요) |
| `test_community_comments.py` | 댓글 (CRUD, 좋아요) |
| `test_search.py` | 검색 (통합, 사건/이슈/게시글) |
| `test_home.py` | 홈 (속보, 인기글, 트렌딩 등) |
| `test_tags.py` | 태그 (목록, 관리자 CRUD) |
| `test_sources.py` | 출처 (목록, 생성, 삭제) |
| `test_tracking.py` | 트래킹 (추적 이슈, 저장 사건) |

## 스케줄러

`trend-korea-worker`로 실행되는 백그라운드 작업입니다.

| 작업 | 주기 | 설명 |
|------|------|------|
| `issue_status_reconcile` | 30분마다 | 이슈 상태 자동 조정 (ongoing/closed/reignited) |
| `search_rankings` | 매시 정각 | 검색 키워드 랭킹 재계산 |
| `community_hot_score` | 10분마다 | 게시글 인기 점수 업데이트 |
| `cleanup_refresh_tokens` | 매일 03:00 KST | 만료된 리프레시 토큰 정리 |

## 데이터베이스

### 마이그레이션

```bash
# 마이그레이션 적용
uv run alembic upgrade head

# 새 마이그레이션 자동 생성
uv run alembic revision --autogenerate -m "변경 설명"
```

> `AUTO_CREATE_TABLES=true` (기본값)이면 서버 시작 시 테이블을 자동으로 생성합니다.
> 운영 환경에서는 `false`로 설정하고 Alembic 마이그레이션을 사용하세요.

### 페이지네이션

| 방식 | 사용처 | 파라미터 |
|------|--------|----------|
| 커서 기반 | 사건, 커뮤니티, 검색 | `cursor`, `limit` → `next_cursor`, `hasMore` |
| 페이지 기반 | 이슈, 출처, 트래킹 | `page`, `limit` → `currentPage`, `totalPages`, `hasNext` |

## API 문서

서버 실행 후 자동 생성되는 API 문서를 확인할 수 있습니다.

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 스크립트

`pyproject.toml`에 정의된 진입점:

| 명령어 | 설명 |
|--------|------|
| `trend-korea-api` | FastAPI 개발 서버 실행 |
| `trend-korea-worker` | APScheduler 백그라운드 워커 실행 |
| `trend-korea-crawl-keywords` | 뉴스 키워드 크롤러 CLI |

## 자주 쓰는 명령어

```bash
uv run trend-korea-api              # 개발 서버
uv run trend-korea-worker           # 스케줄러 워커
uv run alembic upgrade head         # DB 마이그레이션 적용
uv run alembic revision --autogenerate -m "msg"  # 마이그레이션 생성
uv run ruff check src/              # 린트 검사
uv run ruff format src/             # 코드 포매팅
uv run pytest                       # 테스트 실행
```

## 라이선스

Private
