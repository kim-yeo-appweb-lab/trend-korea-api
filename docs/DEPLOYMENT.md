# 클라우드타입 배포 가이드

trend-korea-api를 클라우드타입에서 Dockerfile 기반으로 배포하는 가이드.

## 아키텍처 개요

```
클라우드타입 컨테이너 (단일)
┌─────────────────────────────────┐
│  docker-entrypoint.sh           │
│  ┌────────────┐ ┌─────────────┐ │
│  │ uvicorn    │ │ APScheduler │ │      ┌──────────────┐
│  │ (API 서버) │ │ (워커)      │ │──────│ PostgreSQL   │
│  │ :8000      │ │             │ │      │ (클라우드타입│
│  └────────────┘ └─────────────┘ │      │  or 외부)    │
└─────────────────────────────────┘      └──────────────┘
```

- **API 서버** — FastAPI + Uvicorn, 포트 8000
- **워커** — APScheduler 기반 크론 스케줄러 (이슈 상태 조정, 검색 랭킹, 핫스코어 등)
- 두 프로세스가 하나의 컨테이너에서 동시 실행됨

## 사전 요구사항

- 클라우드타입 계정
- GitHub 저장소 연결
- PostgreSQL 데이터베이스 (클라우드타입 내부 또는 외부)

## 1단계: 클라우드타입 프로젝트 생성

1. 클라우드타입 대시보드에서 **새 프로젝트** 생성
2. GitHub 저장소 연결: `trend-korea-api`
3. 배포 방식: **Dockerfile** 선택

## 2단계: PostgreSQL 설정

### 클라우드타입 내부 DB 사용 시

1. 같은 프로젝트에 **PostgreSQL** 서비스 추가
2. 생성 후 제공되는 연결 문자열을 복사
3. 형식을 `postgresql+psycopg://` 프리픽스로 변환:

```
# 클라우드타입 제공 형식
postgresql://user:password@host:port/dbname

# DATABASE_URL에 입력할 형식
postgresql+psycopg://user:password@host:port/dbname
```

> `+psycopg`는 SQLAlchemy가 psycopg3 드라이버를 사용하기 위해 필요하다.

### 외부 DB 사용 시

Supabase, Neon, AWS RDS 등 외부 PostgreSQL의 연결 문자열을 동일하게 `postgresql+psycopg://` 형식으로 변환하여 사용한다.

## 3단계: 환경변수 설정

클라우드타입 대시보드 → 서비스 설정 → **환경변수**에서 아래 항목을 입력한다.

### 필수 환경변수

| 변수명 | 값 예시 | 설명 |
|--------|---------|------|
| `DATABASE_URL` | `postgresql+psycopg://user:pw@host:5432/trend_korea` | PostgreSQL 연결 문자열 |
| `JWT_SECRET_KEY` | `$(openssl rand -hex 32)` | JWT 서명 키 (최소 16자) |
| `APP_ENV` | `production` | 애플리케이션 환경 |
| `CORS_ORIGINS` | `https://your-frontend.cloudtype.app` | 허용할 프론트엔드 도메인 (쉼표 구분) |

### 선택 환경변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `RUN_MIGRATIONS` | `false` | `true`로 설정 시 컨테이너 시작 시 Alembic 마이그레이션 실행 |
| `APP_HOST` | `0.0.0.0` | 바인드 호스트 |
| `APP_PORT` | `8000` | 바인드 포트 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | 액세스 토큰 만료 시간 (분) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | 리프레시 토큰 만료 시간 (일) |
| `SCHEDULER_TIMEZONE` | `Asia/Seoul` | 스케줄러 타임존 |
| `AUTO_CREATE_TABLES` | `true` | SQLAlchemy 자동 테이블 생성 |

### JWT_SECRET_KEY 생성 방법

로컬 터미널에서 실행 후 출력된 값을 사용한다:

```bash
openssl rand -hex 32
```

## 4단계: 배포 설정

클라우드타입 대시보드에서 설정:

| 항목 | 값 |
|------|-----|
| **포트** | `8000` |
| **Dockerfile 경로** | `Dockerfile` (기본값) |
| **브랜치** | `main` |

## 5단계: 첫 배포

### 데이터베이스 마이그레이션

첫 배포 시에는 `RUN_MIGRATIONS=true` 환경변수를 설정한 뒤 배포한다.
컨테이너 시작 시 `alembic upgrade head`가 실행되어 테이블이 생성된다.

마이그레이션 완료 후에는 `RUN_MIGRATIONS`를 `false`로 변경하거나 삭제해도 된다.
이후 스키마 변경이 있을 때만 다시 `true`로 설정한다.

### 배포 실행

클라우드타입에서 **배포** 버튼을 클릭하면:

1. Dockerfile 기반 이미지 빌드
2. 컨테이너 시작 → `docker-entrypoint.sh` 실행
3. (RUN_MIGRATIONS=true인 경우) Alembic 마이그레이션 실행
4. API 서버 + 워커 동시 시작
5. 헬스체크(`/health/live`) 통과 후 트래픽 수신 시작

## 6단계: 배포 확인

### 헬스체크 확인

```bash
curl https://your-service.cloudtype.app/health/live
```

응답 예시:
```json
{
  "success": true,
  "data": { "status": "ok" }
}
```

### API 문서 확인

```
https://your-service.cloudtype.app/docs
```

FastAPI의 Swagger UI에서 전체 API 엔드포인트를 확인할 수 있다.

## Docker 구성 파일 설명

### Dockerfile

```
python:3.11-slim-bookworm
├── 시스템 패키지: libxml2, libxslt1.1, curl
├── non-root 사용자: appuser (UID 1000)
├── 의존성 설치: pip-compile → requirements.txt → pip install
├── 소스 복사 + entry point 등록: pip install --no-deps
└── HEALTHCHECK: /health/live (30초 간격)
```

- `pip-compile`로 pyproject.toml에서 requirements.txt를 생성하여 설치
- 소스 코드 변경 시에도 pyproject.toml이 그대로면 의존성 레이어가 캐싱됨
- `[crawler]` 옵션 의존성(httpx, beautifulsoup4, lxml, kiwipiepy) 포함

### docker-entrypoint.sh

- `RUN_MIGRATIONS=true`일 때만 `alembic upgrade head` 실행
- uvicorn(API)과 trend-korea-worker(스케줄러)를 백그라운드로 동시 실행
- `trap`으로 SIGTERM/SIGINT를 두 프로세스에 전파
- `wait -n`으로 어느 프로세스든 종료되면 나머지도 정리 → 컨테이너 재시작

### .dockerignore

.git, .env, __pycache__, IDE 설정 파일 등을 빌드 컨텍스트에서 제외하여 빌드 속도를 높이고 민감 정보 유출을 방지한다.

## 로컬 Docker 빌드 테스트

클라우드타입 배포 전에 로컬에서 빌드를 검증할 수 있다:

```bash
# 이미지 빌드
docker build -t trend-korea-api .

# 이미지 크기 확인 (약 400~500MB 예상)
docker images trend-korea-api

# 컨테이너 실행 (로컬 PostgreSQL 필요)
docker run --rm \
  -e DATABASE_URL="postgresql+psycopg://postgres:postgres@host.docker.internal:5432/trend_korea" \
  -e JWT_SECRET_KEY="local-test-secret-key-minimum-16" \
  -e APP_ENV="local" \
  -p 8000:8000 \
  trend-korea-api
```

## 트러블슈팅

### 컨테이너가 계속 재시작되는 경우

1. 클라우드타입 로그에서 에러 메시지 확인
2. `DATABASE_URL` 형식이 `postgresql+psycopg://`로 시작하는지 확인
3. PostgreSQL 서비스가 정상 실행 중인지 확인
4. `JWT_SECRET_KEY`가 16자 이상인지 확인

### 마이그레이션 실패

1. `DATABASE_URL`이 올바른지 확인
2. DB에 연결 가능한 상태인지 확인
3. 클라우드타입 내부 DB를 사용하는 경우, 같은 프로젝트 내에서 네트워크 접근이 가능한지 확인

### CORS 에러

`CORS_ORIGINS` 환경변수에 프론트엔드 도메인이 정확히 포함되어 있는지 확인한다. 여러 도메인은 쉼표로 구분한다:

```
https://frontend.cloudtype.app,https://www.example.com
```

### 워커가 실행되지 않는 경우

로그에서 `trend-korea-worker` 관련 에러를 확인한다. 워커는 `[crawler]` 의존성이 필요하므로, Dockerfile에서 `.[crawler]`로 설치되었는지 확인한다.
