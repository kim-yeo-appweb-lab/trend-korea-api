"""users 도메인 테스트"""

from uuid import uuid4

from starlette.testclient import TestClient


# ── GET /api/v1/users/me ──


def test_me_조회_성공(client: TestClient, member_user: dict, auth_headers: dict):
    """인증된 사용자가 내 정보를 조회하면 200"""
    resp = client.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "조회 성공"
    assert body["data"]["id"] == member_user["user"].id
    assert body["data"]["email"] == member_user["user"].email
    assert body["data"]["nickname"] == member_user["user"].nickname
    assert body["data"]["role"] == "member"
    assert "createdAt" in body["data"]
    assert "timestamp" in body


def test_me_조회_토큰없음_401(client: TestClient):
    """토큰 없이 내 정보를 조회하면 401"""
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── PATCH /api/v1/users/me ──


def test_me_닉네임변경_성공(client: TestClient, auth_headers: dict):
    """닉네임을 변경하면 200"""
    new_nickname = f"변경_{uuid4().hex[:6]}"
    resp = client.patch(
        "/api/v1/users/me",
        json={"nickname": new_nickname},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["nickname"] == new_nickname


def test_me_프로필이미지변경_성공(client: TestClient, auth_headers: dict):
    """프로필 이미지를 변경하면 200"""
    image_url = "https://example.com/new-profile.jpg"
    resp = client.patch(
        "/api/v1/users/me",
        json={"profileImage": image_url},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["profileImage"] == image_url


def test_me_닉네임중복_409(
    client: TestClient, member_user: dict, admin_user: dict, auth_headers: dict
):
    """다른 사용자가 사용 중인 닉네임으로 변경하면 409"""
    resp = client.patch(
        "/api/v1/users/me",
        json={"nickname": admin_user["user"].nickname},
        headers=auth_headers,
    )
    assert resp.status_code == 409

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_CONFLICT_002"


def test_me_수정_토큰없음_401(client: TestClient):
    """토큰 없이 내 정보를 수정하면 401"""
    resp = client.patch("/api/v1/users/me", json={"nickname": "새닉네임"})
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── POST /api/v1/users/me/change-password ──


def test_비밀번호변경_성공(client: TestClient, member_user: dict, auth_headers: dict):
    """현재 비밀번호를 올바르게 입력하면 변경 성공"""
    resp = client.post(
        "/api/v1/users/me/change-password",
        json={
            "currentPassword": member_user["password"],
            "newPassword": "NewSecureP@ss456",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "비밀번호 변경 성공"


def test_비밀번호변경_현재비밀번호불일치_401(client: TestClient, auth_headers: dict):
    """현재 비밀번호가 틀리면 401"""
    resp = client.post(
        "/api/v1/users/me/change-password",
        json={
            "currentPassword": "WrongP@ss999",
            "newPassword": "NewSecureP@ss456",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


def test_비밀번호변경_토큰없음_401(client: TestClient):
    """토큰 없이 비밀번호를 변경하면 401"""
    resp = client.post(
        "/api/v1/users/me/change-password",
        json={
            "currentPassword": "OldP@ss123",
            "newPassword": "NewP@ss456",
        },
    )
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── POST /api/v1/users/me/social-connect ──


def test_social_connect_성공(client: TestClient, auth_headers: dict):
    """SNS 계정 연동 스텁 엔드포인트 동작 확인"""
    resp = client.post(
        "/api/v1/users/me/social-connect",
        json={"provider": "kakao", "code": "test_oauth_code"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["socialProviders"] == ["kakao"]


# ── DELETE /api/v1/users/me/social-disconnect ──


def test_social_disconnect_성공(client: TestClient, auth_headers: dict):
    """SNS 계정 연동 해제 스텁 엔드포인트 동작 확인"""
    resp = client.request(
        "DELETE",
        "/api/v1/users/me/social-disconnect",
        json={"provider": "kakao"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["socialProviders"] == []


# ── GET /api/v1/users/me/activity ──


def test_activity_조회_성공(client: TestClient, auth_headers: dict):
    """활동 내역 스텁 엔드포인트 - 빈 목록 반환"""
    resp = client.get("/api/v1/users/me/activity", headers=auth_headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []
    assert body["data"]["pagination"]["currentPage"] == 1
    assert body["data"]["pagination"]["totalItems"] == 0


# ── GET /api/v1/users/{user_id} ──


def test_사용자조회_성공(client: TestClient, member_user: dict):
    """사용자 ID로 공개 프로필 조회"""
    user_id = member_user["user"].id
    resp = client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] == user_id
    assert body["data"]["nickname"] == member_user["user"].nickname
    assert "activityStats" in body["data"]


def test_사용자조회_존재하지않는ID_404(client: TestClient):
    """존재하지 않는 사용자 ID로 조회하면 404"""
    fake_id = str(uuid4())
    resp = client.get(f"/api/v1/users/{fake_id}")
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_RESOURCE_005"
