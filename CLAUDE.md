# CLAUDE.md

## 프로젝트 개요

대한민국 사회 이슈·사건을 추적·분석하는 FastAPI 백엔드 API.

진입점 3개:
- `trend-korea-api` → `src/main.py:run`
- `trend-korea-worker` → `src/worker_main.py:run`
- `trend-korea-crawl-keywords` → `src/keyword_crawler/cli.py:main`

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
├── utils/             # 의존성 주입, 에러 핸들러, 소셜 인증
├── scheduler/         # 스케줄러 잡 정의
└── keyword_crawler/   # 뉴스 키워드 크롤러
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
- `db/__init__.py` — 모든 모델 배럴 import (Alembic이 모델을 인식하기 위해 필수)
- `db/session.py` — SQLAlchemy 엔진·세션 팩토리
- `utils/` — 의존성 주입, 에러 핸들러, 소셜 인증 등 공용 유틸리티

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
uv run alembic upgrade head         # DB 마이그레이션 적용
uv run alembic revision --autogenerate -m "msg"  # 마이그레이션 생성
uv run ruff check src/              # 린트 검사
uv run ruff format src/             # 코드 포매팅
uv run pytest                       # 테스트 실행
```
