# 이슈(Issue) 도메인 API 테스트

from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from src.db.enums import IssueStatus, SourceEntityType

API = "/api/v1/issues"


# ── GET /api/v1/issues ──


class TestListIssues:
    """이슈 목록 조회 테스트"""

    def test_list_issues_empty(self, client: TestClient):
        """데이터 없을 때 빈 목록 반환"""
        resp = client.get(API)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["items"] == []

    def test_list_issues_with_data(self, client: TestClient, create_issue):
        """데이터가 있을 때 목록 반환"""
        create_issue(title="이슈1")
        create_issue(title="이슈2")
        resp = client.get(API)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]["items"]) == 2

    def test_list_issues_filter_status(self, client: TestClient, create_issue):
        """상태 필터링"""
        create_issue(title="진행 중", status=IssueStatus.ONGOING)
        create_issue(title="종료", status=IssueStatus.CLOSED)
        resp = client.get(API, params={"status": "ongoing"})
        assert resp.status_code == 200
        body = resp.json()
        items = body["data"]["items"]
        assert len(items) == 1
        assert items[0]["status"] == "ongoing"

    def test_list_issues_pagination_info(self, client: TestClient, create_issue):
        """페이지네이션 정보 포함 확인"""
        for i in range(5):
            create_issue(title=f"이슈{i}")
        resp = client.get(API, params={"page": 1, "limit": 2})
        assert resp.status_code == 200
        body = resp.json()
        pagination = body["data"]["pagination"]
        assert pagination["currentPage"] == 1
        assert pagination["totalItems"] == 5
        assert pagination["hasNext"] is True


# ── GET /api/v1/issues/{id} ──


class TestGetIssue:
    """이슈 상세 조회 테스트"""

    def test_get_issue_success(self, client: TestClient, create_issue):
        """존재하는 이슈 상세 조회"""
        issue = create_issue(title="상세 조회 이슈")
        resp = client.get(f"{API}/{issue.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == issue.id
        assert body["data"]["title"] == "상세 조회 이슈"

    def test_get_issue_not_found(self, client: TestClient):
        """존재하지 않는 이슈 404 반환"""
        fake_id = str(uuid4())
        resp = client.get(f"{API}/{fake_id}")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "E_RESOURCE_002"


# ── POST /api/v1/issues (관리자) ──


class TestCreateIssue:
    """이슈 생성 테스트 (관리자 전용)"""

    @pytest.fixture()
    def _source(self, create_source):
        return create_source(entity_type=SourceEntityType.ISSUE)

    def test_create_issue_success(self, client: TestClient, admin_headers, _source):
        """관리자가 이슈 정상 생성 201"""
        payload = {
            "title": "새 이슈",
            "description": "새 이슈 설명입니다.",
            "status": "ongoing",
            "tagIds": [],
            "sourceIds": [_source.id],
            "relatedEventIds": [],
        }
        resp = client.post(API, json=payload, headers=admin_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["title"] == "새 이슈"
        assert body["data"]["status"] == "ongoing"

    def test_create_issue_missing_fields(self, client: TestClient, admin_headers):
        """필수 필드 누락 시 400 반환"""
        payload = {"title": "제목만"}
        resp = client.post(API, json=payload, headers=admin_headers)
        assert resp.status_code == 400

    def test_create_issue_member_forbidden(self, client: TestClient, auth_headers, _source):
        """일반 사용자가 이슈 생성 시 403"""
        payload = {
            "title": "일반 사용자 이슈",
            "description": "설명",
            "status": "ongoing",
            "tagIds": [],
            "sourceIds": [_source.id],
            "relatedEventIds": [],
        }
        resp = client.post(API, json=payload, headers=auth_headers)
        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "E_PERM_002"


# ── PATCH /api/v1/issues/{id} (관리자) ──


class TestUpdateIssue:
    """이슈 수정 테스트 (관리자 전용)"""

    def test_update_issue_success(self, client: TestClient, create_issue, admin_headers):
        """관리자가 이슈 정상 수정"""
        issue = create_issue(title="수정 전")
        payload = {"title": "수정 후"}
        resp = client.patch(f"{API}/{issue.id}", json=payload, headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["title"] == "수정 후"

    def test_update_issue_not_found(self, client: TestClient, admin_headers):
        """존재하지 않는 이슈 수정 404"""
        fake_id = str(uuid4())
        payload = {"title": "수정 시도"}
        resp = client.patch(f"{API}/{fake_id}", json=payload, headers=admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "E_RESOURCE_002"

    def test_update_issue_member_forbidden(self, client: TestClient, create_issue, auth_headers):
        """일반 사용자가 이슈 수정 시 403"""
        issue = create_issue()
        payload = {"title": "일반 사용자 수정"}
        resp = client.patch(f"{API}/{issue.id}", json=payload, headers=auth_headers)
        assert resp.status_code == 403


# ── DELETE /api/v1/issues/{id} (관리자) ──


class TestDeleteIssue:
    """이슈 삭제 테스트 (관리자 전용)"""

    def test_delete_issue_success(self, client: TestClient, create_issue, admin_headers):
        """관리자가 이슈 정상 삭제"""
        issue = create_issue()
        resp = client.delete(f"{API}/{issue.id}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        # 삭제 후 조회 시 404
        resp2 = client.get(f"{API}/{issue.id}")
        assert resp2.status_code == 404

    def test_delete_issue_not_found(self, client: TestClient, admin_headers):
        """존재하지 않는 이슈 삭제 404"""
        fake_id = str(uuid4())
        resp = client.delete(f"{API}/{fake_id}", headers=admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "E_RESOURCE_002"

    def test_delete_issue_member_forbidden(self, client: TestClient, create_issue, auth_headers):
        """일반 사용자가 이슈 삭제 시 403"""
        issue = create_issue()
        resp = client.delete(f"{API}/{issue.id}", headers=auth_headers)
        assert resp.status_code == 403


# ── GET /api/v1/issues/{id}/triggers ──


class TestListTriggers:
    """이슈 트리거 목록 조회 테스트"""

    def test_list_triggers_empty(self, client: TestClient, create_issue):
        """트리거 없는 이슈의 트리거 목록 조회"""
        issue = create_issue()
        resp = client.get(f"{API}/{issue.id}/triggers")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_list_triggers_with_data(self, client: TestClient, create_issue, create_trigger):
        """트리거가 있는 이슈의 트리거 목록 조회"""
        issue = create_issue()
        create_trigger(issue_id=issue.id, summary="트리거1")
        create_trigger(issue_id=issue.id, summary="트리거2")
        resp = client.get(f"{API}/{issue.id}/triggers")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 2


# ── POST /api/v1/issues/{id}/track ──


class TestTrackIssue:
    """이슈 추적 테스트"""

    def test_track_issue_success(self, client: TestClient, create_issue, auth_headers):
        """정상 이슈 추적"""
        issue = create_issue()
        resp = client.post(f"{API}/{issue.id}/track", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["issueId"] == issue.id
        assert body["data"]["isTracking"] is True

    def test_track_issue_already_tracked(self, client: TestClient, create_issue, auth_headers):
        """이미 추적 중인 이슈 409"""
        issue = create_issue()
        client.post(f"{API}/{issue.id}/track", headers=auth_headers)
        resp = client.post(f"{API}/{issue.id}/track", headers=auth_headers)
        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "E_CONFLICT_002"

    def test_track_issue_not_found(self, client: TestClient, auth_headers):
        """존재하지 않는 이슈 추적 404"""
        fake_id = str(uuid4())
        resp = client.post(f"{API}/{fake_id}/track", headers=auth_headers)
        assert resp.status_code == 404

    def test_track_issue_no_token(self, client: TestClient, create_issue):
        """토큰 없이 이슈 추적 시도 401"""
        issue = create_issue()
        resp = client.post(f"{API}/{issue.id}/track")
        assert resp.status_code == 401


# ── DELETE /api/v1/issues/{id}/track ──


class TestUntrackIssue:
    """이슈 추적 해제 테스트"""

    def test_untrack_issue_success(self, client: TestClient, create_issue, auth_headers):
        """정상 이슈 추적 해제"""
        issue = create_issue()
        client.post(f"{API}/{issue.id}/track", headers=auth_headers)
        resp = client.delete(f"{API}/{issue.id}/track", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    def test_untrack_issue_not_found(self, client: TestClient, auth_headers):
        """존재하지 않는 이슈 추적 해제 404"""
        fake_id = str(uuid4())
        resp = client.delete(f"{API}/{fake_id}/track", headers=auth_headers)
        assert resp.status_code == 404

    def test_untrack_issue_no_token(self, client: TestClient, create_issue):
        """토큰 없이 이슈 추적 해제 시도 401"""
        issue = create_issue()
        resp = client.delete(f"{API}/{issue.id}/track")
        assert resp.status_code == 401


# ── POST /api/v1/issues/{id}/triggers (관리자) ──


class TestCreateTrigger:
    """이슈 트리거 생성 테스트 (관리자 전용)"""

    @pytest.fixture()
    def _source(self, create_source):
        return create_source(entity_type=SourceEntityType.TRIGGER)

    def test_create_trigger_success(self, client: TestClient, create_issue, admin_headers, _source):
        """관리자가 트리거 정상 생성 201"""
        issue = create_issue()
        payload = {
            "occurredAt": "2025-06-15T14:00:00Z",
            "summary": "새 트리거 요약",
            "type": "article",
            "sourceIds": [_source.id],
        }
        resp = client.post(f"{API}/{issue.id}/triggers", json=payload, headers=admin_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["summary"] == "새 트리거 요약"
        assert body["data"]["issueId"] == issue.id

    def test_create_trigger_issue_not_found(self, client: TestClient, admin_headers, _source):
        """존재하지 않는 이슈에 트리거 생성 404"""
        fake_id = str(uuid4())
        payload = {
            "occurredAt": "2025-06-15T14:00:00Z",
            "summary": "트리거",
            "type": "article",
            "sourceIds": [_source.id],
        }
        resp = client.post(f"{API}/{fake_id}/triggers", json=payload, headers=admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "E_RESOURCE_002"

    def test_create_trigger_member_forbidden(
        self, client: TestClient, create_issue, auth_headers, _source
    ):
        """일반 사용자가 트리거 생성 시 403"""
        issue = create_issue()
        payload = {
            "occurredAt": "2025-06-15T14:00:00Z",
            "summary": "트리거",
            "type": "article",
            "sourceIds": [_source.id],
        }
        resp = client.post(f"{API}/{issue.id}/triggers", json=payload, headers=auth_headers)
        assert resp.status_code == 403
