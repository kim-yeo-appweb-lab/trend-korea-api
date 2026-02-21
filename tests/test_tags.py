# 태그 도메인 API 테스트

from src.db.enums import TagType


class TestListTags:
    """GET /api/v1/tags 테스트"""

    def test_list_tags_empty(self, client):
        """태그가 없으면 빈 목록 반환"""
        res = client.get("/api/v1/tags")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_list_tags_with_data(self, client, create_tag):
        """태그가 있으면 목록 반환"""
        create_tag(name="정치", tag_type=TagType.CATEGORY, slug="politics")
        create_tag(name="서울", tag_type=TagType.REGION, slug="seoul")
        res = client.get("/api/v1/tags")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        item = body["data"][0]
        assert "id" in item
        assert "name" in item
        assert "type" in item
        assert "slug" in item

    def test_list_tags_filter_by_type(self, client, create_tag):
        """type 파라미터로 태그 유형 필터링"""
        create_tag(name="경제", tag_type=TagType.CATEGORY, slug="economy")
        create_tag(name="부산", tag_type=TagType.REGION, slug="busan")
        res = client.get("/api/v1/tags", params={"type": "category"})
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        for tag in body["data"]:
            assert tag["type"] == "category"

    def test_list_tags_search(self, client, create_tag):
        """search 파라미터로 태그 이름 검색"""
        create_tag(name="사회", tag_type=TagType.CATEGORY, slug="society")
        create_tag(name="문화", tag_type=TagType.CATEGORY, slug="culture")
        res = client.get("/api/v1/tags", params={"search": "사회"})
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) >= 1
        assert any(t["name"] == "사회" for t in body["data"])


class TestCreateTag:
    """POST /api/v1/tags 테스트"""

    def test_create_tag_admin(self, client, admin_headers):
        """관리자가 태그를 생성하면 201 반환"""
        payload = {"name": "테스트태그", "type": "category", "slug": "test-tag"}
        res = client.post("/api/v1/tags", json=payload, headers=admin_headers)
        assert res.status_code == 201
        body = res.json()
        assert body["success"] is True
        assert body["data"]["name"] == "테스트태그"
        assert body["data"]["type"] == "category"
        assert body["data"]["slug"] == "test-tag"

    def test_create_tag_member_forbidden(self, client, auth_headers):
        """일반 사용자가 태그 생성 시 403 반환"""
        payload = {"name": "금지태그", "type": "category", "slug": "forbidden"}
        res = client.post("/api/v1/tags", json=payload, headers=auth_headers)
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False

    def test_create_tag_no_token(self, client):
        """토큰 없이 태그 생성 시 401 반환"""
        payload = {"name": "비인증", "type": "category", "slug": "no-auth"}
        res = client.post("/api/v1/tags", json=payload)
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False


class TestUpdateTag:
    """PATCH /api/v1/tags/{id} 테스트"""

    def test_update_tag_admin(self, client, admin_headers, create_tag):
        """관리자가 태그를 수정하면 200 반환"""
        tag = create_tag(name="수정전", slug="before-update")
        res = client.patch(
            f"/api/v1/tags/{tag.id}",
            json={"name": "수정후"},
            headers=admin_headers,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["name"] == "수정후"

    def test_update_tag_not_found(self, client, admin_headers):
        """존재하지 않는 태그 수정 시 404 반환"""
        res = client.patch(
            "/api/v1/tags/nonexistent-id",
            json={"name": "없는태그"},
            headers=admin_headers,
        )
        assert res.status_code == 404
        body = res.json()
        assert body["success"] is False

    def test_update_tag_member_forbidden(self, client, auth_headers, create_tag):
        """일반 사용자가 태그 수정 시 403 반환"""
        tag = create_tag(name="수정금지")
        res = client.patch(
            f"/api/v1/tags/{tag.id}",
            json={"name": "변경시도"},
            headers=auth_headers,
        )
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False


class TestDeleteTag:
    """DELETE /api/v1/tags/{id} 테스트"""

    def test_delete_tag_admin(self, client, admin_headers, create_tag):
        """관리자가 태그를 삭제하면 200 반환"""
        tag = create_tag(name="삭제태그")
        res = client.delete(f"/api/v1/tags/{tag.id}", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

    def test_delete_tag_not_found(self, client, admin_headers):
        """존재하지 않는 태그 삭제 시 404 반환"""
        res = client.delete("/api/v1/tags/nonexistent-id", headers=admin_headers)
        assert res.status_code == 404
        body = res.json()
        assert body["success"] is False

    def test_delete_tag_member_forbidden(self, client, auth_headers, create_tag):
        """일반 사용자가 태그 삭제 시 403 반환"""
        tag = create_tag(name="삭제금지")
        res = client.delete(f"/api/v1/tags/{tag.id}", headers=auth_headers)
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False
