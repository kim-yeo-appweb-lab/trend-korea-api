# CLAUDE.md

## 프로젝트 개요

대한민국 사회 이슈·사건을 추적·분석하는 FastAPI 백엔드 API.

진입점 3개:
- `trend-korea-api` → `src/trend_korea/main.py:run`
- `trend-korea-worker` → `src/trend_korea/worker_main.py:run`
- `trend-korea-crawl-keywords` → `src/trend_korea/keyword_crawler/cli.py:main`

## 기술 스택

- 패키지 매니저: **uv**
- 프레임워크: **FastAPI** (Python 3.11+)
- ORM: **SQLAlchemy 2.0** (sync Session)
- 검증: **Pydantic V2** + pydantic-settings
- DB: **PostgreSQL 16**
- 마이그레이션: **Alembic**
- 스케줄러: **APScheduler**
- 인증: **JWT** (python-jose, passlib[bcrypt])
- 린터: **ruff** (line-length=100, target=py311)

## 아키텍처

도메인 기반(Domain-based) 폴더 구조를 사용합니다.

```
src/trend_korea/
├── core/              # 설정(config.py), 로깅, 공통 응답
├── db/                # Base 모델, 세션, 공유 모델 + 배럴 import
├── shared/            # 에러 핸들러, 페이지네이션 등 공용 유틸
├── auth/              # 인증 도메인
├── users/             # 사용자 도메인
├── events/            # 사건 도메인
├── issues/            # 이슈 도메인
├── community/         # 커뮤니티 도메인 (게시글, 댓글)
├── search/            # 검색 도메인
├── tracking/          # 트래킹 도메인
├── home/              # 홈 도메인
├── tags/              # 태그 도메인
├── sources/           # 출처 도메인
├── triggers/          # 트리거 도메인
├── scheduler/         # 스케줄러 잡 정의
└── keyword_crawler/   # 뉴스 키워드 크롤러
```

### 도메인 디렉터리 패턴

각 도메인은 다음 파일로 구성됩니다:
- `router.py` — FastAPI 라우터 (엔드포인트)
- `schemas.py` — Pydantic V2 요청/응답 스키마
- `models.py` — SQLAlchemy 2.0 모델
- `service.py` — 비즈니스 로직
- `repository.py` — 데이터 액세스 계층

### 공유 레이어

- `core/config.py` — pydantic-settings 기반 환경변수 (`Settings` 클래스)
- `db/__init__.py` — 모든 모델 배럴 import (Alembic이 모델을 인식하기 위해 필수)
- `db/session.py` — SQLAlchemy 엔진·세션 팩토리
- `shared/` — 도메인 간 공용 유틸리티

## 주요 컨벤션

### 코드 스타일

- ruff: line-length=100, target-version=py311
- 타입 힌트 필수 (`X | None` 스타일, `Optional[X]` 사용 금지)
- SQLAlchemy 2.0 `select()` 스타일 (`session.query()` 사용 금지)
- Pydantic V2 문법 (`field_validator`, `model_validator`, `model_config`)
- `Annotated` 패턴으로 의존성 주입

### Import 규칙

- 도메인 간 참조: `from trend_korea.{domain}.{module} import ...`
- ForeignKey는 테이블명 문자열 참조: `ForeignKey("users.id")`
- `db/__init__.py`에서 모든 모델을 배럴 import (새 모델 추가 시 반드시 등록)
- import 순서: 표준 라이브러리 → 외부 패키지 → 프로젝트 내부

### 파일 명명

- 모델: `{domain}/models.py`
- 스키마: `{domain}/schemas.py`
- 라우터: `{domain}/router.py`
- 서비스: `{domain}/service.py`
- 저장소: `{domain}/repository.py`

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

# 개발 서버 (auto-reload)
uv run trend-korea-api

# 스케줄러 워커
uv run trend-korea-worker

# 키워드 크롤러
uv run trend-korea-crawl-keywords --top-n 30 --save-db
```

필수 환경변수: `DATABASE_URL` (예: `postgresql://postgres:postgres@localhost:5432/trend_korea`)

## 테스트

```bash
# 전체 테스트
uv run pytest

# 특정 파일
uv run pytest tests/test_auth.py -v

# 커버리지
uv run pytest --cov=trend_korea
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
uv run alembic upgrade head         # DB 마이그레이션 적용
uv run alembic revision --autogenerate -m "msg"  # 마이그레이션 생성
uv run ruff check src/              # 린트 검사
uv run ruff format src/             # 코드 포매팅
uv run pytest                       # 테스트 실행
```
