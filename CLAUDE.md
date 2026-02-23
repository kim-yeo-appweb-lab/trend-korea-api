# CLAUDE.md

## 프로젝트 개요

대한민국 사회 이슈·사건을 추적·분석하는 FastAPI 백엔드 API.

진입점 6개:
- `trend-korea-api` → `src/main.py:run`
- `trend-korea-worker` → `src/worker_main.py:run`
- `trend-korea-crawl-keywords` → `src/utils/keyword_crawler/cli.py:main`
- `trend-korea-crawl-news` → `src/utils/news_crawler/cli.py:main`
- `trend-korea-summarize-news` → `src/utils/news_summarizer/cli.py:main`
- `trend-korea-full-cycle` → `src/utils/pipeline/cli.py:main`

## 기술 스택

- 패키지 매니저: **uv**
- 프레임워크: **FastAPI** (Python 3.11+)
- ORM: **SQLAlchemy 2.0** (sync Session)
- 검증: **Pydantic V2** + pydantic-settings
- DB: **PostgreSQL 16**
- 마이그레이션: **Alembic**
- 스케줄러: **APScheduler**
- 인증: **JWT** (python-jose, bcrypt)
- 린터: **ruff** (line-length=100, target=py311)

## 아키텍처

레이어 기반(Layer-based) 폴더 구조를 사용합니다.

```
src/
├── main.py            # FastAPI 앱 진입점
├── worker_main.py     # APScheduler 워커 진입점
├── api/v1/            # 라우터 (엔드포인트)
├── models/            # SQLAlchemy 2.0 모델
├── schemas/           # Pydantic V2 요청/응답 스키마
├── crud/              # 비즈니스 로직 (서비스)
├── sql/               # 데이터 액세스 계층 (레포지토리)
├── core/              # 설정, 보안, 예외, 로깅, 페이지네이션
├── db/                # Base 모델, 세션, enum, 배럴 import
├── utils/             # 공용 유틸리티 + 파이프라인 모듈
│   ├── dependencies.py          # 의존성 주입
│   ├── error_handlers.py        # 에러 핸들러
│   ├── social/                  # 소셜 인증
│   ├── keyword_crawler/         # 뉴스 키워드 크롤러
│   ├── news_crawler/            # 외부 뉴스 파이프라인 래퍼
│   ├── news_summarizer/         # Ollama LLM 뉴스 요약
│   └── pipeline/                # 전체 파이프라인 오케스트레이터
└── scheduler/         # 스케줄러 잡 정의
```

### 레이어 디렉터리 패턴

각 레이어는 도메인별 파일로 구성됩니다:
- `api/v1/{domain}.py` — FastAPI 라우터 (엔드포인트)
- `schemas/{domain}.py` — Pydantic V2 요청/응답 스키마
- `models/{domain}.py` — SQLAlchemy 2.0 모델
- `crud/{domain}.py` — 비즈니스 로직
- `sql/{domain}.py` — 데이터 액세스 계층

### 공유 레이어

- `core/config.py` — pydantic-settings 기반 환경변수 (`Settings` 클래스)
- `core/security.py` — 비밀번호 해싱, JWT 토큰 검증
- `core/exceptions.py` — 커스텀 `AppError` 예외 클래스
- `core/response.py` — 표준 응답 래퍼 (`success_response`)
- `core/pagination.py` — 커서 기반 페이지네이션 유틸리티
- `db/__init__.py` — 모든 모델 배럴 import (Alembic이 모델을 인식하기 위해 필수)
- `db/session.py` — SQLAlchemy 엔진·세션 팩토리
- `db/enums.py` — 공유 Enum 정의
- `utils/dependencies.py` — `DbSession`, `CurrentMemberUserId`, `CurrentAdminUserId`
- `utils/error_handlers.py` — 글로벌 예외 핸들러
- `utils/social/` — 소셜 인증 프로바이더 (카카오, 네이버, 구글)
- `utils/keyword_crawler/` — 뉴스 키워드 크롤러
- `utils/news_crawler/` — 외부 뉴스 파이프라인 래퍼
- `utils/news_summarizer/` — Ollama LLM 뉴스 요약
- `utils/pipeline/` — 전체 파이프라인 오케스트레이터

### 도메인 목록

`auth` | `users` | `events` | `issues` | `triggers` | `community` | `search` | `tracking` | `home` | `tags` | `sources`

## 주요 컨벤션

### 코드 스타일

- ruff: line-length=100, target-version=py311
- 타입 힌트 필수 (`X | None` 스타일, `Optional[X]` 사용 금지)
- SQLAlchemy 2.0 `select()` 스타일 (`session.query()` 사용 금지)
- Pydantic V2 문법 (`field_validator`, `model_validator`, `model_config`)
- `Annotated` 패턴으로 의존성 주입

### Import 규칙

- 레이어 참조: `from src.{layer}.{domain} import ...`
- 예시:
  - `from src.models.users import User`
  - `from src.schemas.events import CreateEventRequest`
  - `from src.crud.issues import IssueService`
  - `from src.sql.auth import AuthRepository`
  - `from src.api.v1.auth import router`
- ForeignKey는 테이블명 문자열 참조: `ForeignKey("users.id")`
- `db/__init__.py`에서 모든 모델을 배럴 import (새 모델 추가 시 반드시 등록)
- import 순서: 표준 라이브러리 → 외부 패키지 → 프로젝트 내부

### 파일 명명

- 모델: `models/{domain}.py`
- 스키마: `schemas/{domain}.py`
- 라우터: `api/v1/{domain}.py`
- 서비스: `crud/{domain}.py`
- 저장소: `sql/{domain}.py`

### 응답 형식

성공: `{"success": true, "data": {...}, "message": "...", "timestamp": "..."}`
에러: `{"success": false, "error": {"code": "E_XXX_000", "message": "..."}, "timestamp": "..."}`

### 에러 코드 접두사

- `E_AUTH_` — 인증 (비밀번호 오류, 토큰 만료/무효)
- `E_PERM_` — 권한 (작성자 아님, 관리자 필요)
- `E_VALID_` — 검증 (필수 필드 누락, 포맷 오류)
- `E_RESOURCE_` — 리소스 미존재 (001~007: event, issue, post, comment, user, tag, trigger)
- `E_CONFLICT_` — 충돌 (이메일 중복, 이미 추적/저장)
- `E_SERVER_` — 서버 내부 오류

### 페이지네이션

- 커서 기반: 사건(events), 커뮤니티(community), 검색(search) — `cursor`, `limit`
- 페이지 기반: 이슈(issues), 출처(sources), 트래킹(tracking) — `page`, `limit`

### 인증 구조

- JWT HS256, Access Token 60분, Refresh Token 14일
- 권한: Public (비인증) / Member (Bearer) / Admin (Bearer + admin 역할)
- SNS 로그인: 카카오, 네이버, 구글 (OAuth)

## 스케줄러 잡

| 잡 이름 | 주기 | 설명 |
|---------|------|------|
| `issue_status_reconcile` | 30분 | 이슈 상태 조정 |
| `search_rankings` | 매시 정각 | 검색 랭킹 재계산 |
| `community_hot_score` | 10분 | 인기 게시글 점수 업데이트 |
| `cleanup_refresh_tokens` | 매일 03:00 | 만료 토큰 정리 |

## 커밋 규칙

Conventional Commits, 한국어, 50자 이내.

### 타입

`feat` | `fix` | `refactor` | `docs` | `test` | `chore` | `perf` | `style` | `migration`

### 스코프

`auth` | `users` | `events` | `issues` | `community` | `search` | `tags` | `sources` | `triggers` | `tracking` | `home` | `crawler` | `worker` | `config` | `db`

### 규칙

- 이모지 사용 금지
- .env 파일 커밋 금지 (.env.example만 커밋)
- 한꺼번에 커밋하지 않고 작은 작업 단위로 분리
- body는 선택사항이며, 필요시 "왜" 변경했는지 설명

## 빌드/실행

```bash
# 의존성 설치
uv sync

# 크롤러 포함 설치
uv sync --extra crawler

# 요약기 포함 설치
uv sync --extra summarizer

# 전체 (크롤러 + 요약기)
uv sync --extra crawler --extra summarizer

# 개발 서버 (auto-reload)
uv run trend-korea-api

# 스케줄러 워커
uv run trend-korea-worker

# 키워드 크롤러
uv run trend-korea-crawl-keywords --top-n 30 --save-db

# 뉴스 크롤링 (외부 파이프라인)
uv run trend-korea-crawl-news --keyword "키워드" --limit 3

# 뉴스 요약
uv run trend-korea-summarize-news --input news.json --model gemma3:4b

# 전체 파이프라인 (키워드→크롤링→요약)
uv run trend-korea-full-cycle --repeat 1 --max-keywords 3
```

필수 환경변수: `DATABASE_URL` (예: `postgresql://postgres:postgres@localhost:5432/trend_korea`)

## 테스트

```bash
# 전체 테스트
uv run pytest

# 특정 파일
uv run pytest tests/test_auth.py -v

# 커버리지
uv run pytest --cov=src
```

테스트 스택: pytest + httpx (sync TestClient)

## 데이터베이스 마이그레이션

```bash
# 마이그레이션 적용
uv run alembic upgrade head

# 새 마이그레이션 생성
uv run alembic revision --autogenerate -m "변경 설명"
```

## 자주 쓰는 명령어

```bash
uv run trend-korea-api              # 개발 서버
uv run trend-korea-worker           # 스케줄러 워커
uv run trend-korea-crawl-keywords   # 키워드 크롤러
uv run trend-korea-crawl-news       # 뉴스 크롤링
uv run trend-korea-summarize-news   # 뉴스 요약
uv run trend-korea-full-cycle       # 전체 파이프라인
uv run alembic upgrade head         # DB 마이그레이션 적용
uv run alembic revision --autogenerate -m "msg"  # 마이그레이션 생성
uv run ruff check src/              # 린트 검사
uv run ruff format src/             # 코드 포매팅
uv run pytest                       # 테스트 실행
```
