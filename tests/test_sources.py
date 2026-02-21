# 출처 도메인 API 테스트


class TestListSources:
    """GET /api/v1/sources 테스트"""

    def test_list_sources_empty(self, client):
        """출처가 없으면 빈 목록 반환"""
        res = client.get("/api/v1/sources")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["pagination"]["totalItems"] == 0

    def test_list_sources_with_data(self, client, create_source):
        """출처가 있으면 목록 반환"""
        create_source(title="뉴스 1", publisher="한국일보")
        create_source(title="뉴스 2", publisher="조선일보")
        res = client.get("/api/v1/sources")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]["items"]) == 2
        item = body["data"]["items"][0]
        assert "id" in item
        assert "title" in item
        assert "url" in item
        assert "publisher" in item
        assert "publishedAt" in item

    def test_list_sources_filter_by_publisher(self, client, create_source):
        """publisher 파라미터로 매체 필터링"""
        create_source(title="기사 A", publisher="한국일보")
        create_source(title="기사 B", publisher="중앙일보")
        res = client.get("/api/v1/sources", params={"publisher": "한국일보"})
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        for item in body["data"]["items"]:
            assert item["publisher"] == "한국일보"


class TestCreateSource:
    """POST /api/v1/sources 테스트"""

    def test_create_source_admin(self, client, admin_headers):
        """관리자가 출처를 등록하면 201 반환"""
        payload = {
            "url": "https://example.com/article/1",
            "title": "테스트 기사",
            "publisher": "테스트일보",
            "publishedAt": "2025-06-15T09:00:00Z",
        }
        res = client.post("/api/v1/sources", json=payload, headers=admin_headers)
        assert res.status_code == 201
        body = res.json()
        assert body["success"] is True
        assert body["data"]["title"] == "테스트 기사"
        assert body["data"]["publisher"] == "테스트일보"

    def test_create_source_member_forbidden(self, client, auth_headers):
        """일반 사용자가 출처 등록 시 403 반환"""
        payload = {
            "url": "https://example.com/forbidden",
            "title": "금지 기사",
            "publisher": "금지일보",
            "publishedAt": "2025-06-15T09:00:00Z",
        }
        res = client.post("/api/v1/sources", json=payload, headers=auth_headers)
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False

    def test_create_source_no_token(self, client):
        """토큰 없이 출처 등록 시 401 반환"""
        payload = {
            "url": "https://example.com/no-auth",
            "title": "비인증 기사",
            "publisher": "비인증일보",
            "publishedAt": "2025-06-15T09:00:00Z",
        }
        res = client.post("/api/v1/sources", json=payload)
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False


class TestDeleteSource:
    """DELETE /api/v1/sources/{id} 테스트"""

    def test_delete_source_admin(self, client, admin_headers, create_source):
        """관리자가 출처를 삭제하면 200 반환"""
        source = create_source(title="삭제 대상")
        res = client.delete(f"/api/v1/sources/{source.id}", headers=admin_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

    def test_delete_source_not_found(self, client, admin_headers):
        """존재하지 않는 출처 삭제 시 404 반환"""
        res = client.delete("/api/v1/sources/nonexistent-id", headers=admin_headers)
        assert res.status_code == 404
        body = res.json()
        assert body["success"] is False

    def test_delete_source_member_forbidden(self, client, auth_headers, create_source):
        """일반 사용자가 출처 삭제 시 403 반환"""
        source = create_source(title="삭제 금지")
        res = client.delete(f"/api/v1/sources/{source.id}", headers=auth_headers)
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False
