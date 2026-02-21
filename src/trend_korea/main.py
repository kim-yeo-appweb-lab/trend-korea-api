from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from trend_korea.api.error_handlers import register_exception_handlers
from trend_korea.api.routers.v1 import auth, community, events, home, issues, me, search, sources, tags, tracking, triggers, users
from trend_korea.core.config import get_settings
from trend_korea.core.logging import configure_logging
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.models import Base
from trend_korea.infrastructure.db.session import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description="""
## 트렌드 코리아 API

대한민국 사회 이슈·사건을 실시간으로 추적·분석하는 플랫폼의 백엔드 API입니다.

### 인증 방법

`Authorization: Bearer <accessToken>` 헤더를 포함하여 요청합니다.
- **accessToken**은 로그인(`POST /auth/login`) 또는 회원가입(`POST /auth/register`) 응답에서 발급됩니다.
- 토큰 만료 시 `POST /auth/refresh`로 갱신합니다.

### 에러 코드 체계

| 접두사 | 의미 | 예시 |
|--------|------|------|
| `E_AUTH_` | 인증 관련 | `E_AUTH_001` 토큰 없음, `E_AUTH_003` 유효하지 않은 토큰 |
| `E_PERM_` | 권한 관련 | `E_PERM_001` 작성자 아님, `E_PERM_002` 관리자 필요 |
| `E_VALID_` | 유효성 검증 | `E_VALID_001` 필수 필드 누락, `E_VALID_002` 형식 오류 |
| `E_RESOURCE_` | 리소스 조회 | `E_RESOURCE_001` ~ `E_RESOURCE_007` (각 엔티티 미발견) |
| `E_CONFLICT_` | 중복/충돌 | `E_CONFLICT_001` 중복, `E_CONFLICT_002` 이미 추적 중 |
| `E_SERVER_` | 서버 오류 | `E_SERVER_001` 내부 오류 |

### 공통 응답 형식

**성공 응답:**
```json
{
  "success": true,
  "data": { ... },
  "message": "요청 성공",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

**에러 응답:**
```json
{
  "success": false,
  "error": { "code": "E_...", "message": "...", "details": {} },
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```
""",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "인증 · 회원가입, 로그인, 토큰 갱신, SNS 로그인, 회원탈퇴"},
        {"name": "users", "description": "사용자 · 내 정보 조회/수정, 비밀번호 변경, SNS 연동, 활동 내역"},
        {"name": "events", "description": "사건 · 사건 목록/상세 조회, 저장/해제, 관리자 CRUD"},
        {"name": "issues", "description": "이슈 · 이슈 목록/상세 조회, 추적/해제, 관리자 CRUD, 트리거 관리"},
        {"name": "posts", "description": "게시글 · 게시글 목록/상세 조회, 작성/수정/삭제, 추천"},
        {"name": "comments", "description": "댓글 · 댓글 목록 조회, 작성/수정/삭제, 좋아요"},
        {"name": "search", "description": "검색 · 통합 검색, 사건/이슈/게시글 검색"},
        {"name": "tracking", "description": "트래킹 · 추적 중인 이슈, 저장한 사건 목록 조회"},
        {"name": "home", "description": "홈 · 속보, 인기 게시글, 검색 랭킹, 트렌딩, 타임라인, 주요 뉴스"},
        {"name": "tags", "description": "태그 · 태그 목록 조회, 관리자 CRUD"},
        {"name": "sources", "description": "출처 · 출처 목록 조회, 관리자 등록/삭제"},
        {"name": "triggers", "description": "트리거 · 트리거 수정/삭제 (관리자 전용)"},
    ],
    servers=[{"url": "/", "description": "현재 서버"}],
    license_info={"name": "Private"},
)

configure_logging()
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.get("/health/live", summary="Liveness 체크", tags=["health"])
def health_live(request: Request):
    return success_response(request=request, data={"status": "ok"})


@app.get("/health/ready", summary="Readiness 체크", tags=["health"])
def health_ready(request: Request):
    return success_response(request=request, data={"status": "ok"})


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(me.router, prefix=settings.api_v1_prefix)
app.include_router(events.router, prefix=settings.api_v1_prefix)
app.include_router(issues.router, prefix=settings.api_v1_prefix)
app.include_router(community.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(tracking.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(home.router, prefix=settings.api_v1_prefix)
app.include_router(tags.router, prefix=settings.api_v1_prefix)
app.include_router(sources.router, prefix=settings.api_v1_prefix)
app.include_router(triggers.router, prefix=settings.api_v1_prefix)


def run() -> None:
    import uvicorn

    uvicorn.run(
        "trend_korea.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "local",
    )
