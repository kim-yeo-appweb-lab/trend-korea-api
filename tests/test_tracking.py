# 트래킹 도메인 API 테스트


class TestTrackedIssues:
    """GET /api/v1/users/me/tracked-issues 테스트"""

    def test_tracked_issues_empty(self, client, auth_headers):
        """추적 중인 이슈가 없으면 빈 목록 반환"""
        res = client.get("/api/v1/users/me/tracked-issues", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["pagination"]["totalItems"] == 0

    def test_tracked_issues_with_data(self, client, auth_headers, create_issue):
        """이슈를 추적하면 추적 목록에 나타남"""
        issue = create_issue(title="추적 이슈")
        # 이슈 추적 시작
        client.post(f"/api/v1/issues/{issue.id}/track", headers=auth_headers)
        res = client.get("/api/v1/users/me/tracked-issues", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["pagination"]["totalItems"] >= 1

    def test_tracked_issues_no_token(self, client):
        """토큰 없이 추적 이슈 조회 시 401 반환"""
        res = client.get("/api/v1/users/me/tracked-issues")
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False


class TestSavedEvents:
    """GET /api/v1/users/me/saved-events 테스트"""

    def test_saved_events_empty(self, client, auth_headers):
        """저장한 사건이 없으면 빈 목록 반환"""
        res = client.get("/api/v1/users/me/saved-events", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["pagination"]["totalItems"] == 0

    def test_saved_events_with_data(self, client, auth_headers, create_event):
        """사건을 저장하면 저장 목록에 나타남"""
        event = create_event(title="저장 사건")
        # 사건 저장
        client.post(f"/api/v1/events/{event.id}/save", headers=auth_headers)
        res = client.get("/api/v1/users/me/saved-events", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["pagination"]["totalItems"] >= 1

    def test_saved_events_no_token(self, client):
        """토큰 없이 저장 사건 조회 시 401 반환"""
        res = client.get("/api/v1/users/me/saved-events")
        assert res.status_code == 401
        body = res.json()
        assert body["success"] is False
