"""community 댓글 도메인 테스트"""

from uuid import uuid4

from starlette.testclient import TestClient


# ── GET /api/v1/posts/{id}/comments ──


def test_list_comments_빈목록(client: TestClient, member_user: dict, create_post):
    """댓글이 없는 게시글의 댓글 목록은 빈 배열"""
    post = create_post(author_id=member_user["user"].id)

    resp = client.get(f"/api/v1/posts/{post.id}/comments")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"] == []


def test_list_comments_데이터있음(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """댓글이 있으면 목록에 포함"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id, content="테스트 댓글")

    resp = client.get(f"/api/v1/posts/{post.id}/comments")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]
    assert len(items) >= 1
    assert any(item["id"] == comment.id for item in items)
    assert items[0]["content"] == "테스트 댓글"
    assert items[0]["postId"] == post.id


# ── POST /api/v1/posts/{id}/comments ──


def test_create_comment_성공(client: TestClient, member_user: dict, create_post):
    """정상적으로 댓글 생성 시 201"""
    post = create_post(author_id=member_user["user"].id)
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.post(
        f"/api/v1/posts/{post.id}/comments",
        json={"content": "새 댓글입니다."},
        headers=headers,
    )
    assert resp.status_code == 201

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "댓글 생성 성공"
    assert body["data"]["content"] == "새 댓글입니다."
    assert body["data"]["postId"] == post.id
    assert body["data"]["parentId"] is None


def test_create_comment_대댓글(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """parentId를 지정하면 대댓글 생성"""
    post = create_post(author_id=member_user["user"].id)
    parent = create_comment(post_id=post.id, author_id=member_user["user"].id, content="부모 댓글")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.post(
        f"/api/v1/posts/{post.id}/comments",
        json={"content": "대댓글입니다.", "parentId": parent.id},
        headers=headers,
    )
    assert resp.status_code == 201

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["parentId"] == parent.id
    assert body["data"]["content"] == "대댓글입니다."


def test_create_comment_게시글미존재_404(client: TestClient, auth_headers: dict):
    """존재하지 않는 게시글에 댓글 작성 시 404"""
    resp = client.post(
        f"/api/v1/posts/{uuid4()}/comments",
        json={"content": "댓글"},
        headers=auth_headers,
    )
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_RESOURCE_003"


def test_create_comment_토큰없음_401(client: TestClient, member_user: dict, create_post):
    """토큰 없이 댓글 작성하면 401"""
    post = create_post(author_id=member_user["user"].id)

    resp = client.post(
        f"/api/v1/posts/{post.id}/comments",
        json={"content": "인증 없는 댓글"},
    )
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── PATCH /api/v1/comments/{id} ──


def test_update_comment_정상수정(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """작성자 본인이 댓글 수정"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id, content="원본 댓글")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.patch(
        f"/api/v1/comments/{comment.id}",
        json={"content": "수정된 댓글"},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["content"] == "수정된 댓글"
    assert body["data"]["id"] == comment.id


def test_update_comment_다른사용자_403(
    client: TestClient, member_user: dict, admin_user: dict, create_post, create_comment
):
    """다른 사용자가 댓글 수정 시도하면 403"""
    post = create_post(author_id=admin_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=admin_user["user"].id, content="관리자 댓글")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.patch(
        f"/api/v1/comments/{comment.id}",
        json={"content": "수정 시도"},
        headers=headers,
    )
    assert resp.status_code == 403

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_PERM_001"


def test_update_comment_관리자는_수정가능(
    client: TestClient, member_user: dict, admin_user: dict, create_post, create_comment
):
    """관리자는 다른 사용자의 댓글을 수정할 수 있음"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(
        post_id=post.id, author_id=member_user["user"].id, content="일반 사용자 댓글"
    )
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    resp = client.patch(
        f"/api/v1/comments/{comment.id}",
        json={"content": "관리자가 수정"},
        headers=headers,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["content"] == "관리자가 수정"


def test_update_comment_미존재_404(client: TestClient, auth_headers: dict):
    """존재하지 않는 댓글 수정 시 404"""
    resp = client.patch(
        f"/api/v1/comments/{uuid4()}",
        json={"content": "존재하지 않는 댓글"},
        headers=auth_headers,
    )
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False


def test_update_comment_토큰없음_401(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """토큰 없이 댓글 수정하면 401"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id)

    resp = client.patch(f"/api/v1/comments/{comment.id}", json={"content": "수정"})
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── DELETE /api/v1/comments/{id} ──


def test_delete_comment_정상삭제(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """작성자 본인이 댓글 삭제"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id, content="삭제할 댓글")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.delete(f"/api/v1/comments/{comment.id}", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "댓글 삭제 성공"


def test_delete_comment_다른사용자_403(
    client: TestClient, member_user: dict, admin_user: dict, create_post, create_comment
):
    """다른 사용자가 댓글 삭제 시도하면 403"""
    post = create_post(author_id=admin_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=admin_user["user"].id, content="관리자 댓글")
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.delete(f"/api/v1/comments/{comment.id}", headers=headers)
    assert resp.status_code == 403

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_PERM_001"


def test_delete_comment_관리자는_삭제가능(
    client: TestClient, member_user: dict, admin_user: dict, create_post, create_comment
):
    """관리자는 다른 사용자의 댓글을 삭제할 수 있음"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(
        post_id=post.id, author_id=member_user["user"].id, content="삭제 대상 댓글"
    )
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    resp = client.delete(f"/api/v1/comments/{comment.id}", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True


def test_delete_comment_토큰없음_401(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """토큰 없이 댓글 삭제하면 401"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id)

    resp = client.delete(f"/api/v1/comments/{comment.id}")
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── POST /api/v1/comments/{id}/like ──


def test_like_comment_성공(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """댓글 좋아요 성공"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id)
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    resp = client.post(f"/api/v1/comments/{comment.id}/like", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["commentId"] == comment.id
    assert body["data"]["likeCount"] == 1
    assert body["data"]["userLiked"] is True


def test_like_comment_미존재_404(client: TestClient, auth_headers: dict):
    """존재하지 않는 댓글에 좋아요하면 404"""
    resp = client.post(f"/api/v1/comments/{uuid4()}/like", headers=auth_headers)
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_RESOURCE_004"


def test_like_comment_토큰없음_401(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """토큰 없이 좋아요하면 401"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id)

    resp = client.post(f"/api/v1/comments/{comment.id}/like")
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"


# ── DELETE /api/v1/comments/{id}/like ──


def test_unlike_comment_성공(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """댓글 좋아요 취소 성공"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id)
    headers = {"Authorization": f"Bearer {member_user['token']}"}

    # 먼저 좋아요
    client.post(f"/api/v1/comments/{comment.id}/like", headers=headers)

    # 좋아요 취소
    resp = client.delete(f"/api/v1/comments/{comment.id}/like", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["commentId"] == comment.id
    assert body["data"]["likeCount"] == 0
    assert body["data"]["userLiked"] is False


def test_unlike_comment_미존재_404(client: TestClient, auth_headers: dict):
    """존재하지 않는 댓글에 좋아요 취소하면 404"""
    resp = client.delete(f"/api/v1/comments/{uuid4()}/like", headers=auth_headers)
    assert resp.status_code == 404

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_RESOURCE_004"


def test_unlike_comment_토큰없음_401(
    client: TestClient, member_user: dict, create_post, create_comment
):
    """토큰 없이 좋아요 취소하면 401"""
    post = create_post(author_id=member_user["user"].id)
    comment = create_comment(post_id=post.id, author_id=member_user["user"].id)

    resp = client.delete(f"/api/v1/comments/{comment.id}/like")
    assert resp.status_code == 401

    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "E_AUTH_001"
