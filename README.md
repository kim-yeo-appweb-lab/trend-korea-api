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
| 검증 | Pydantic V2 |
| 데이터베이스 | PostgreSQL 16 |
| 마이그레이션 | Alembic |
| 스케줄러 | APScheduler |
| 인증 | JWT (python-jose) |
| 패키지 매니저 | uv |

## 시작하기

### 사전 요구사항

- Python 3.11+
- PostgreSQL 15+
- [uv](https://docs.astral.sh/uv/)

### 설치

```bash
git clone <repository-url>
cd trend-korea-api
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

```
src/trend_korea/
├── main.py                 # FastAPI 앱 진입점
├── worker_main.py          # 스케줄러 워커 진입점
├── core/                   # 설정, 로깅, 공통 응답
├── db/                     # Base, 세션, 공유 모델 (CrawledKeyword, JobRun 등)
├── shared/                 # 공용 유틸 (에러 핸들러, 페이지네이션 등)
├── auth/                   # 인증 (회원가입, 로그인, 토큰 갱신, SNS 로그인)
├── users/                  # 사용자 (프로필, 비밀번호 변경, SNS 연동)
├── events/                 # 사건 (목록/상세, 저장/해제, 관리자 CRUD)
├── issues/                 # 이슈 (목록/상세, 추적/해제, 관리자 CRUD)
├── community/              # 커뮤니티 (게시글, 댓글, 추천)
├── search/                 # 검색 (통합 검색, 랭킹)
├── tracking/               # 트래킹 (추적 이슈, 저장 사건 목록)
├── home/                   # 홈 (속보, 인기 게시글, 트렌딩 등)
├── tags/                   # 태그
├── sources/                # 출처
├── triggers/               # 트리거
├── scheduler/              # 스케줄러 잡 정의
└── keyword_crawler/        # 뉴스 키워드 크롤러
```

각 도메인 디렉터리는 일반적으로 다음 파일들로 구성됩니다:

- `router.py` — API 엔드포인트
- `schemas.py` — Pydantic 요청/응답 스키마
- `models.py` — SQLAlchemy 모델
- `service.py` — 비즈니스 로직
- `repository.py` — 데이터 액세스

## API 문서

서버 실행 후 자동 생성되는 API 문서를 확인할 수 있습니다.

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 헬스체크

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /health/live` | Liveness 체크 |
| `GET /health/ready` | Readiness 체크 |

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

## 스크립트

`pyproject.toml`에 정의된 진입점:

| 명령어 | 설명 |
|--------|------|
| `trend-korea-api` | FastAPI 개발 서버 실행 |
| `trend-korea-worker` | APScheduler 백그라운드 워커 실행 |
| `trend-korea-crawl-keywords` | 뉴스 키워드 크롤러 CLI |

## 라이선스

Private
