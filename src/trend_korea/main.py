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


app = FastAPI(title=settings.app_name, lifespan=lifespan)

configure_logging()
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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


@app.get("/health/live")
def health_live(request: Request):
    return success_response(request=request, data={"status": "ok"})


@app.get("/health/ready")
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
