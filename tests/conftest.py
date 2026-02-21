# 환경변수를 모든 import보다 먼저 설정해야 함
# db/session.py가 모듈 레벨에서 get_settings()를 호출하기 때문
import os

os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-jwt-testing"

from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from src.core.security import create_access_token, hash_password
from src.db import Base
from src.db.enums import (
    Importance,
    IssueStatus,
    SourceEntityType,
    TagType,
    TriggerType,
    UserRole,
    VerificationStatus,
)
from src.main import app
from src.utils.dependencies import get_db_session

# SQLite in-memory 엔진 (StaticPool로 커넥션 공유)
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# SQLite에서 FK 제약 활성화
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── 세션 스코프: 테이블 생성/삭제 ──


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ── 함수 스코프: 트랜잭션 격리 ──


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── 사용자 fixture ──

_TEST_PASSWORD = "TestP@ss1234"


@pytest.fixture()
def member_user(db_session: Session) -> dict:
    """일반 사용자를 생성하고 {user, token, password}를 반환"""
    from src.models.users import User

    user_id = str(uuid4())
    now = datetime.now(timezone.utc)
    user = User(
        id=user_id,
        nickname=f"member_{uuid4().hex[:6]}",
        email=f"member_{uuid4().hex[:6]}@test.com",
        password_hash=hash_password(_TEST_PASSWORD),
        role=UserRole.MEMBER,
        is_active=True,
        withdrawn_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()
    token = create_access_token(user_id, "member")
    return {"user": user, "token": token, "password": _TEST_PASSWORD}


@pytest.fixture()
def admin_user(db_session: Session) -> dict:
    """관리자 사용자를 생성하고 {user, token, password}를 반환"""
    from src.models.users import User

    user_id = str(uuid4())
    now = datetime.now(timezone.utc)
    user = User(
        id=user_id,
        nickname=f"admin_{uuid4().hex[:6]}",
        email=f"admin_{uuid4().hex[:6]}@test.com",
        password_hash=hash_password(_TEST_PASSWORD),
        role=UserRole.ADMIN,
        is_active=True,
        withdrawn_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()
    token = create_access_token(user_id, "admin")
    return {"user": user, "token": token, "password": _TEST_PASSWORD}


@pytest.fixture()
def auth_headers(member_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {member_user['token']}"}


@pytest.fixture()
def admin_headers(admin_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_user['token']}"}


# ── 팩토리 fixture ──


@pytest.fixture()
def create_tag(db_session: Session):
    """태그 팩토리: create_tag(name, tag_type, slug) -> Tag"""
    from src.models.tags import Tag

    def _factory(
        name: str = "테스트태그",
        tag_type: TagType = TagType.CATEGORY,
        slug: str | None = None,
    ) -> Tag:
        tag = Tag(
            id=str(uuid4()),
            name=name,
            type=tag_type,
            slug=slug or f"test-{uuid4().hex[:8]}",
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(tag)
        db_session.flush()
        return tag

    return _factory


@pytest.fixture()
def create_source(db_session: Session):
    """출처 팩토리: create_source(...) -> Source"""
    from src.models.sources import Source

    def _factory(
        url: str = "https://example.com/news",
        title: str = "테스트 뉴스",
        publisher: str = "테스트일보",
        entity_type: SourceEntityType = SourceEntityType.EVENT,
        entity_id: str = "manual",
    ) -> Source:
        source = Source(
            id=str(uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            url=url,
            title=title,
            publisher=publisher,
            published_at=datetime.now(timezone.utc),
        )
        db_session.add(source)
        db_session.flush()
        return source

    return _factory


@pytest.fixture()
def create_event(db_session: Session):
    """사건 팩토리: create_event(...) -> Event"""
    from src.models.events import Event

    def _factory(
        title: str = "테스트 사건",
        summary: str = "테스트 사건 요약",
        importance: Importance = Importance.MEDIUM,
        verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
    ) -> Event:
        now = datetime.now(timezone.utc)
        evt = Event(
            id=str(uuid4()),
            occurred_at=now,
            title=title,
            summary=summary,
            importance=importance,
            verification_status=verification_status,
            source_count=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(evt)
        db_session.flush()
        return evt

    return _factory


@pytest.fixture()
def create_issue(db_session: Session):
    """이슈 팩토리: create_issue(...) -> Issue"""
    from src.models.issues import Issue

    def _factory(
        title: str = "테스트 이슈",
        description: str = "테스트 이슈 설명",
        status: IssueStatus = IssueStatus.ONGOING,
    ) -> Issue:
        now = datetime.now(timezone.utc)
        issue = Issue(
            id=str(uuid4()),
            title=title,
            description=description,
            status=status,
            tracker_count=0,
            latest_trigger_at=None,
            created_at=now,
            updated_at=now,
        )
        db_session.add(issue)
        db_session.flush()
        return issue

    return _factory


@pytest.fixture()
def create_trigger(db_session: Session):
    """트리거 팩토리: create_trigger(issue_id, ...) -> Trigger"""
    from src.models.triggers import Trigger

    def _factory(
        issue_id: str,
        summary: str = "테스트 트리거",
        trigger_type: TriggerType = TriggerType.ARTICLE,
    ) -> Trigger:
        now = datetime.now(timezone.utc)
        trigger = Trigger(
            id=str(uuid4()),
            issue_id=issue_id,
            occurred_at=now,
            summary=summary,
            type=trigger_type,
            created_at=now,
            updated_at=now,
        )
        db_session.add(trigger)
        db_session.flush()
        return trigger

    return _factory


@pytest.fixture()
def create_post(db_session: Session):
    """게시글 팩토리: create_post(author_id, ...) -> Post"""
    from src.models.community import Post

    def _factory(
        author_id: str,
        title: str = "테스트 게시글",
        content: str = "테스트 게시글 내용입니다.",
    ) -> Post:
        now = datetime.now(timezone.utc)
        post = Post(
            id=str(uuid4()),
            author_id=author_id,
            title=title,
            content=content,
            is_anonymous=False,
            like_count=0,
            dislike_count=0,
            comment_count=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(post)
        db_session.flush()
        return post

    return _factory


@pytest.fixture()
def create_comment(db_session: Session):
    """댓글 팩토리: create_comment(post_id, author_id, ...) -> Comment"""
    from src.models.community import Comment

    def _factory(
        post_id: str,
        author_id: str,
        content: str = "테스트 댓글",
        parent_id: str | None = None,
    ) -> Comment:
        now = datetime.now(timezone.utc)
        comment = Comment(
            id=str(uuid4()),
            post_id=post_id,
            parent_id=parent_id,
            author_id=author_id,
            content=content,
            like_count=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(comment)
        db_session.flush()
        return comment

    return _factory
