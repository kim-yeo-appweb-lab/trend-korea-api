"""community 게시글 도메인 테스트"""

from uuid import uuid4

from starlette.testclient import TestClient


# ── GET /api/v1/posts ──


def test_list_posts_빈목록(client: TestClient):
    """게시글이 없으면 빈 목록 반환"""
    resp = client.get("/api/v1/posts")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []
    assert body["data"]["cursor"]["hasMore"] is False


def test_list_posts_데이터있음(client: TestClient, member_user: dict, create_post):
    """게시글이 존재하면 목록에 포함"""
    post = create_post(author_id=member_user["user"].id, title="첫번째 게시글")

    resp = client.get("/api/v1/posts")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) >= 1
    assert any(item["id"] == post.id for item in items)


def test_list_posts_페이지네이션(client: TestClient, member_user: dict, create_post):
    """limit 파라미터로 페이지네이션 동작 확인"""
    for i in range(3):
        create_post(author_id=member_user["user"].id, title=f"게시글_{i}")

    resp = client.get("/api/v1/posts", params={"limit": 2})
    assert resp.status_code == 200

    body = resp.json()
    assert len(body["data"]["items"]) == 2
    assert body["data"]["cursor"]["hasMore"] is True


# ── POST /api/v1/posts ──


def test_create_post_성공(client: TestClient, auth_headers: dict):
    """정상적으로 게시글 생성 시 201"""
    payload = {
        "title": "새 게시글",
        "content": "게시글 내용입니다.",
        "tagIds": [],
        "isAnonymous": False,
    }
    resp = client.post("/api/v1/posts", json=payload, headers=auth_headers)
    assert resp.status_code == 201

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "게시글 생성 성공"
    assert body["data"]["title"] == "새 게시글"
    assert body["data"]["content"] == "게시글 내용입니다."
    assert "id" in body["data"]
    assert "createdAt" in body["data"]


def test_create_post_제목누락_400(client: TestClient, auth_headers: dict):
    """제목이 없으면 400 검증 에러"""
    payload = {
        "content": "내용만 있는 게시글",
    }
    resp = client.post("/api/v1/posts", json=payload, headers=auth_headers)
    assert resp.status_code == 400

    body = resp.json()
    assert body["success"] is False


def test_create_post_태그초과_400(client: TestClient, auth_headers: dict):
    """태그가 3개를 초과하면 400"""
    payload = {
        "title": "태그 초과 게시글",
        "content": "내용",
        "tagIds": ["tag1", "tag2", "tag3", "tag4"],
        "isAnonymous": False,
    }
    resp = client.post("/api/v1/posts", json=payload, headers=auth_headers)
    assert resp.status_code == 400

    body = resp.json()
    assert body["success"] is False


def test_create_post_토큰없음_401(client: TestClient):
    """토큰 없이 게시글 생성하면 401"""
    payload = {
        "title": "인증 없는 게시글",
        "content": "내용",
    }
    resp = client.post("/api/v1/posts", json=payload)
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── GET /api/v1/posts/{id} ──


def test_get_post_정상조회(client: TestClient, member_user: dict, create_post):
    """게시글 상세 조회 성공"""
    post = create_post(author_id=member_user["user"].id, title="조회용 게시글")

    resp = client.get(f"/api/v1/posts/{post.id}")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] == post.id
    assert body["data"]["title"] == "조회용 게시글"
    assert "likeCount" in body["data"]
    assert "commentCount" in body["data"]


def test_get_post_미존재_404(client: TestClient):
    """존재하지 않는 게시글 조회 시 404"""
    resp = client.get(f"/api/v1/posts/{uuid4()}")
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_RESOURCE_003"


# ── PATCH /api/v1/posts/{id} ──


def test_update_post_정상수정(client: TestClient, member_user: dict, create_post):
    """작성자 본인이 게시글 수정"""
    post = create_post(author_id=member_user["user"].id, title="원본 제목")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.patch(
        f"/api/v1/posts/{post.id}",
        json={"title": "수정된 제목"},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["title"] == "수정된 제목"


def test_update_post_다른사용자_403(
    client: TestClient, member_user: dict, admin_user: dict, create_post
):
    """다른 사용자가 게시글 수정 시도하면 403"""
    # admin_user가 게시글 작성
    post = create_post(author_id=admin_user["user"].id, title="관리자 게시글")
    # member_user가 수정 시도
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.patch(
        f"/api/v1/posts/{post.id}",
        json={"title": "수정 시도"},
        headers=headers,
    )
    assert resp.status_code == 403

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_PERM_001"


def test_update_post_관리자는_수정가능(
    client: TestClient, member_user: dict, admin_user: dict, create_post
):
    """관리자는 다른 사용자의 게시글을 수정할 수 있음"""
    post = create_post(author_id=member_user["user"].id, title="일반 사용자 게시글")
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    resp = client.patch(
        f"/api/v1/posts/{post.id}",
        json={"title": "관리자가 수정"},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["title"] == "관리자가 수정"


def test_update_post_미존재_404(client: TestClient, auth_headers: dict):
    """존재하지 않는 게시글 수정 시 404"""
    resp = client.patch(
        f"/api/v1/posts/{uuid4()}",
        json={"title": "존재하지 않는 게시글"},
        headers=auth_headers,
    )
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False


def test_update_post_토큰없음_401(client: TestClient, member_user: dict, create_post):
    """토큰 없이 게시글 수정하면 401"""
    post = create_post(author_id=member_user["user"].id)

    resp = client.patch(f"/api/v1/posts/{post.id}", json={"title": "수정"})
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── DELETE /api/v1/posts/{id} ──


def test_delete_post_정상삭제(client: TestClient, member_user: dict, create_post):
    """작성자 본인이 게시글 삭제"""
    post = create_post(author_id=member_user["user"].id, title="삭제할 게시글")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.delete(f"/api/v1/posts/{post.id}", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "게시글 삭제 성공"

    # 삭제 후 조회 시 404
    resp2 = client.get(f"/api/v1/posts/{post.id}")
    assert resp2.status_code == 404


def test_delete_post_다른사용자_403(
    client: TestClient, member_user: dict, admin_user: dict, create_post
):
    """다른 사용자가 게시글 삭제 시도하면 403"""
    post = create_post(author_id=admin_user["user"].id, title="관리자 게시글")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.delete(f"/api/v1/posts/{post.id}", headers=headers)
    assert resp.status_code == 403

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_PERM_001"


def test_delete_post_관리자는_삭제가능(
    client: TestClient, member_user: dict, admin_user: dict, create_post
):
    """관리자는 다른 사용자의 게시글을 삭제할 수 있음"""
    post = create_post(author_id=member_user["user"].id, title="삭제 대상")
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    resp = client.delete(f"/api/v1/posts/{post.id}", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True


def test_delete_post_토큰없음_401(client: TestClient, member_user: dict, create_post):
    """토큰 없이 게시글 삭제하면 401"""
    post = create_post(author_id=member_user["user"].id)

    resp = client.delete(f"/api/v1/posts/{post.id}")
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── POST /api/v1/posts/{id}/like ──


def test_vote_post_추천(client: TestClient, member_user: dict, create_post):
    """게시글 추천(like) 성공"""
    post = create_post(author_id=member_user["user"].id)
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.post(
        f"/api/v1/posts/{post.id}/like",
        json={"type": "like"},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["postId"] == post.id
    assert body["data"]["userAction"] == "like"
    assert body["data"]["likeCount"] == 1


def test_vote_post_비추천(client: TestClient, member_user: dict, create_post):
    """게시글 비추천(dislike) 성공"""
    post = create_post(author_id=member_user["user"].id)
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.post(
        f"/api/v1/posts/{post.id}/like",
        json={"type": "dislike"},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["userAction"] == "dislike"
    assert body["data"]["dislikeCount"] == 1


def test_vote_post_투표변경(client: TestClient, member_user: dict, create_post):
    """추천 후 비추천으로 변경"""
    post = create_post(author_id=member_user["user"].id)
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    # 먼저 추천
    client.post(f"/api/v1/posts/{post.id}/like", json={"type": "like"}, headers=headers)

    # 비추천으로 변경
    resp = client.post(
        f"/api/v1/posts/{post.id}/like",
        json={"type": "dislike"},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["userAction"] == "dislike"
    assert body["data"]["likeCount"] == 0
    assert body["data"]["dislikeCount"] == 1


def test_vote_post_미존재_404(client: TestClient, auth_headers: dict):
    """존재하지 않는 게시글에 투표하면 404"""
    resp = client.post(
        f"/api/v1/posts/{uuid4()}/like",
        json={"type": "like"},
        headers=auth_headers,
    )
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_RESOURCE_003"


def test_vote_post_토큰없음_401(client: TestClient, member_user: dict, create_post):
    """토큰 없이 투표하면 401"""
    post = create_post(author_id=member_user["user"].id)

    resp = client.post(f"/api/v1/posts/{post.id}/like", json={"type": "like"})
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"
