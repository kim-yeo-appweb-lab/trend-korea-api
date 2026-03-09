# CLAUDE.md

## 프로젝트 개요

대한민국 사회 이슈/사건을 추적/분석하는 FastAPI 백엔드 API.

## 기술 스택

- 패키지 매니저: **uv** / 프레임워크: **FastAPI** (Python 3.11+)
- ORM: **SQLAlchemy 2.0** (sync) / 검증: **Pydantic V2**
- DB: **PostgreSQL 16** / 마이그레이션: **Alembic**
- 린터/포매터: **ruff** (line-length=100)

## 아키텍처

레이어 기반 구조. 도메인별 파일로 구성:

```
api/v1/{domain}.py -> schemas/{domain}.py -> crud/{domain}.py -> sql/{domain}.py -> models/{domain}.py
(라우터)             (스키마)                (비즈니스 로직)       (데이터 액세스)     (모델)
```

도메인: `auth` | `users` | `events` | `issues` | `triggers` | `community` | `search` | `tracking` | `home` | `tags` | `sources`

## 검증 명령어

```bash
uv run pytest                    # 테스트
uv run ruff check src/           # 린트
uv run ruff format src/          # 포매팅
uv run alembic upgrade head      # DB 마이그레이션
```

## 서버 실행

```bash
uv run trend-korea-api           # 개발 서버 (:8000)
uv run trend-korea-worker        # 스케줄러 워커
```

## 핵심 규칙

- Import: `from src.{layer}.{domain} import ...`
- 새 모델 추가 시 `db/__init__.py`에 배럴 import 등록 필수
- 필수 환경변수: `DATABASE_URL`
