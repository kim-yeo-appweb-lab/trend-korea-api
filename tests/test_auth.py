"""auth 도메인 테스트"""

from uuid import uuid4

from starlette.testclient import TestClient

from trend_korea.core.security import create_access_token, create_refresh_token


# ── POST /api/v1/auth/register ──


def test_register_성공(client: TestClient):
    """정상 회원가입 시 201 및 토큰 반환"""
    payload = {
        "nickname": "신규유저",
        "email": f"new_{uuid4().hex[:6]}@test.com",
        "password": "SecureP@ss123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "회원가입 성공"
    assert body["data"]["user"]["email"] == payload["email"]
    assert body["data"]["user"]["nickname"] == payload["nickname"]
    assert body["data"]["user"]["role"] == "member"
    assert "accessToken" in body["data"]["tokens"]
    assert "refreshToken" in body["data"]["tokens"]
    assert "timestamp" in body


def test_register_이메일중복_409(client: TestClient, member_user: dict):
    """이미 가입된 이메일로 회원가입하면 409"""
    payload = {
        "nickname": "다른닉네임",
        "email": member_user["user"].email,
        "password": "SecureP@ss123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_CONFLICT_001"


def test_register_닉네임중복_409(client: TestClient, member_user: dict):
    """이미 사용 중인 닉네임으로 회원가입하면 409"""
    payload = {
        "nickname": member_user["user"].nickname,
        "email": f"unique_{uuid4().hex[:6]}@test.com",
        "password": "SecureP@ss123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_CONFLICT_002"


def test_register_짧은비밀번호_400(client: TestClient):
    """비밀번호가 8자 미만이면 400 검증 에러"""
    payload = {
        "nickname": "테스트유저",
        "email": f"short_{uuid4().hex[:6]}@test.com",
        "password": "short",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_VALID_002"


def test_register_잘못된이메일_400(client: TestClient):
    """이메일 형식이 잘못되면 400 검증 에러"""
    payload = {
        "nickname": "테스트유저",
        "email": "not-an-email",
        "password": "SecureP@ss123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400

    body = resp.json()
    assert body["success"] is False


# ── POST /api/v1/auth/login ──


def test_login_성공(client: TestClient, member_user: dict):
    """정상 로그인 시 200 및 토큰 반환"""
    payload = {
        "email": member_user["user"].email,
        "password": member_user["password"],
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "로그인 성공"
    assert body["data"]["user"]["id"] == member_user["user"].id
    assert "accessToken" in body["data"]["tokens"]
    assert "refreshToken" in body["data"]["tokens"]


def test_login_잘못된비밀번호_401(client: TestClient, member_user: dict):
    """비밀번호가 틀리면 401"""
    payload = {
        "email": member_user["user"].email,
        "password": "WrongP@ss999",
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_004"


def test_login_존재하지않는이메일_401(client: TestClient):
    """존재하지 않는 이메일로 로그인하면 401"""
    payload = {
        "email": "nobody@nowhere.com",
        "password": "SecureP@ss123",
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_004"


def test_login_탈퇴계정_401(client: TestClient, member_user: dict):
    """탈퇴한 계정으로 로그인하면 401"""
    # 먼저 탈퇴 처리
    headers = {"Authorization": f"Bearer {member_user['token']}"}
    client.request(
        "DELETE",
        "/api/v1/auth/withdraw",
        json={"password": member_user["password"]},
        headers=headers,
    )

    # 탈퇴한 계정으로 로그인 시도
    payload = {
        "email": member_user["user"].email,
        "password": member_user["password"],
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_006"


# ── POST /api/v1/auth/refresh ──


def test_refresh_성공(client: TestClient, member_user: dict):
    """정상 로그인 후 발급된 refresh token으로 갱신 성공"""
    # 먼저 로그인하여 refresh token 획득
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": member_user["user"].email,
            "password": member_user["password"],
        },
    )
    refresh_token = login_resp.json()["data"]["tokens"]["refreshToken"]

    resp = client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "토큰 갱신 성공"
    assert "accessToken" in body["data"]
    assert "expiresIn" in body["data"]


def test_refresh_잘못된토큰_401(client: TestClient):
    """잘못된 토큰으로 갱신하면 401"""
    resp = client.post("/api/v1/auth/refresh", json={"refreshToken": "invalid.token.here"})
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False


def test_refresh_access토큰으로시도_401(client: TestClient, member_user: dict):
    """access token으로 refresh를 시도하면 401 (typ != refresh)"""
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": member_user["token"]},
    )
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_003"


# ── POST /api/v1/auth/logout ──


def test_logout_성공(client: TestClient, auth_headers: dict):
    """인증된 사용자가 로그아웃하면 200"""
    resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "로그아웃 성공"


def test_logout_토큰없음_401(client: TestClient):
    """토큰 없이 로그아웃하면 401"""
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── GET /api/v1/auth/social/providers ──


def test_social_providers_조회(client: TestClient):
    """SNS 로그인 제공자 목록 조회"""
    resp = client.get("/api/v1/auth/social/providers")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"] == ["kakao", "naver", "google"]


# ── POST /api/v1/auth/social-login ──


def test_social_login_성공(client: TestClient):
    """SNS 로그인 정상 동작 (신규 사용자 자동 가입)"""
    payload = {
        "provider": "kakao",
        "code": "test_auth_code_12345",
        "redirectUri": "https://example.com/callback",
    }
    resp = client.post("/api/v1/auth/social-login", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["isNewUser"] is True
    assert body["data"]["user"]["socialProviders"] == ["kakao"]
    assert "accessToken" in body["data"]["tokens"]


def test_social_login_기존사용자(client: TestClient):
    """이미 SNS 가입한 사용자가 다시 로그인하면 isNewUser=False"""
    payload = {
        "provider": "naver",
        "code": "existing_code_abc",
        "redirectUri": "https://example.com/callback",
    }
    # 첫 번째 로그인 (신규 가입)
    client.post("/api/v1/auth/social-login", json=payload)

    # 두 번째 로그인 (기존 사용자)
    resp = client.post("/api/v1/auth/social-login", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["isNewUser"] is False


def test_social_login_잘못된provider_400(client: TestClient):
    """지원하지 않는 provider로 요청하면 400 검증 에러"""
    payload = {
        "provider": "facebook",
        "code": "test_code",
        "redirectUri": "https://example.com/callback",
    }
    resp = client.post("/api/v1/auth/social-login", json=payload)
    assert resp.status_code == 400

    body = resp.json()
    assert body["success"] is False


# ── DELETE /api/v1/auth/withdraw ──


def test_withdraw_성공(client: TestClient, member_user: dict):
    """정상 탈퇴 처리"""
    headers = {"Authorization": f"Bearer {member_user['token']}"}
    resp = client.request(
        "DELETE",
        "/api/v1/auth/withdraw",
        json={"password": member_user["password"]},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "회원탈퇴 완료"


def test_withdraw_비밀번호불일치_401(client: TestClient, member_user: dict):
    """비밀번호가 틀리면 401"""
    headers = {"Authorization": f"Bearer {member_user['token']}"}
    resp = client.request(
        "DELETE",
        "/api/v1/auth/withdraw",
        json={"password": "WrongP@ss999"},
        headers=headers,
    )
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_004"


def test_withdraw_이미탈퇴_409(client: TestClient, member_user: dict):
    """이미 탈퇴한 계정을 다시 탈퇴 시도하면 409"""
    headers = {"Authorization": f"Bearer {member_user['token']}"}
    # 첫 번째 탈퇴
    client.request(
        "DELETE",
        "/api/v1/auth/withdraw",
        json={"password": member_user["password"]},
        headers=headers,
    )
    # 두 번째 탈퇴 시도
    resp = client.request(
        "DELETE",
        "/api/v1/auth/withdraw",
        json={"password": member_user["password"]},
        headers=headers,
    )
    assert resp.status_code == 409

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_006"


def test_withdraw_토큰없음_401(client: TestClient):
    """토큰 없이 탈퇴하면 401"""
    resp = client.request("DELETE", "/api/v1/auth/withdraw", json={"password": "SecureP@ss123"})
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"
