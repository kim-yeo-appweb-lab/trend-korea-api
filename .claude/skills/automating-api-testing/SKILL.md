---
name: automating-api-testing
description: |
  프로젝트 특화 API 테스트 자동화 스킬. pytest + httpx + sync TestClient 기반으로
  REST API 테스트를 생성합니다. 테스트 작성, 픽스처 설정, 인증 흐름 테스트에 사용합니다.
---

# API 테스트 자동화

pytest + httpx 기반의 FastAPI 테스트 가이드.

## 테스트 실행

```bash
# 전체 테스트
uv run pytest

# 특정 파일
uv run pytest tests/test_auth.py

# 특정 테스트
uv run pytest tests/test_auth.py::test_register -v

# 커버리지
uv run pytest --cov=src/trend_korea --cov-report=term-missing
```

## 디렉터리 구조

```
tests/
├── conftest.py          # 공통 픽스처 (DB 세션, 클라이언트, 인증 헬퍼)
├── test_auth.py         # 인증 엔드포인트 테스트
├── test_users.py        # 사용자 엔드포인트 테스트
└── ...
```

## 핵심 픽스처

### DB 세션 오버라이드 (sync)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from trend_korea.api.deps import get_db_session
from trend_korea.infrastructure.db.models.base import Base
from trend_korea.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session):
    def _override():
        yield db

    app.dependency_overrides[get_db_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

### 인증 헬퍼 픽스처

```python
from trend_korea.core.security import create_access_token


@pytest.fixture
def auth_headers(db: Session) -> dict[str, str]:
    """member 권한 사용자의 인증 헤더를 생성합니다."""
    # 테스트 사용자 생성 (DB에 직접 삽입)
    user = User(id="test-user-id", nickname="tester", email="test@example.com", ...)
    db.add(user)
    db.commit()

    token = create_access_token(user_id=user.id, role="member")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db: Session) -> dict[str, str]:
    """admin 권한 사용자의 인증 헤더를 생성합니다."""
    user = User(id="admin-id", nickname="admin", email="admin@example.com", role=UserRole.admin, ...)
    db.add(user)
    db.commit()

    token = create_access_token(user_id=user.id, role="admin")
    return {"Authorization": f"Bearer {token}"}
```

## 테스트 패턴

### 기본 CRUD 테스트

```python
def test_register_success(client: TestClient):
    response = client.post("/api/v1/auth/register", json={
        "nickname": "newuser",
        "email": "new@example.com",
        "password": "SecurePass123!",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "tokens" in data["data"]


def test_register_duplicate_email(client: TestClient, auth_headers):
    # 이미 존재하는 이메일로 가입 시도
    response = client.post("/api/v1/auth/register", json={
        "nickname": "another",
        "email": "test@example.com",  # auth_headers 픽스처가 생성한 이메일
        "password": "SecurePass123!",
    })
    assert response.status_code == 409
    assert response.json()["success"] is False
```

### 인증 필수 엔드포인트 테스트

```python
def test_protected_endpoint_without_token(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "E_AUTH_001"


def test_protected_endpoint_with_token(client: TestClient, auth_headers):
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### 관리자 전용 엔드포인트 테스트

```python
def test_admin_endpoint_with_member_token(client: TestClient, auth_headers):
    response = client.delete("/api/v1/admin/users/some-id", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "E_PERM_002"


def test_admin_endpoint_with_admin_token(client: TestClient, admin_headers):
    response = client.delete("/api/v1/admin/users/some-id", headers=admin_headers)
    assert response.status_code in (200, 204)
```

## 공통 응답 검증 헬퍼

```python
def assert_success(response, status_code=200):
    assert response.status_code == status_code
    data = response.json()
    assert data["success"] is True
    assert "timestamp" in data
    return data["data"]


def assert_error(response, status_code, error_code=None):
    assert response.status_code == status_code
    data = response.json()
    assert data["success"] is False
    if error_code:
        assert data["error"]["code"] == error_code
    return data["error"]
```

## 주의사항

- 테스트 DB는 SQLite 또는 별도 PostgreSQL 인스턴스 사용
- 각 테스트 함수는 독립적 (function scope fixture)
- `app.dependency_overrides`로 DB 세션 교체
- 인증이 필요한 테스트는 반드시 `auth_headers`/`admin_headers` 픽스처 사용
