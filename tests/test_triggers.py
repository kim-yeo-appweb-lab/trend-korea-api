# 트리거(Trigger) 도메인 API 테스트

from uuid import uuid4

from starlette.testclient import TestClient

API = "/api/v1/triggers"


# ── PATCH /api/v1/triggers/{id} (관리자) ──


class TestUpdateTrigger:
    """트리거 수정 테스트 (관리자 전용)"""

    def test_update_trigger_success(
        self, client: TestClient, create_issue, create_trigger, admin_headers
    ):
        """관리자가 트리거 정상 수정"""
        issue = create_issue()
        trigger = create_trigger(issue_id=issue.id, summary="수정 전")
        payload = {"summary": "수정 후"}
        resp = client.patch(f"{API}/{trigger.id}", json=payload, headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["summary"] == "수정 후"

    def test_update_trigger_not_found(self, client: TestClient, admin_headers):
        """존재하지 않는 트리거 수정 404"""
        fake_id = str(uuid4())
        payload = {"summary": "수정 시도"}
        resp = client.patch(f"{API}/{fake_id}", json=payload, headers=admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "E_RESOURCE_005"

    def test_update_trigger_member_forbidden(
        self, client: TestClient, create_issue, create_trigger, auth_headers
    ):
        """일반 사용자가 트리거 수정 시 403"""
        issue = create_issue()
        trigger = create_trigger(issue_id=issue.id)
        payload = {"summary": "일반 사용자 수정"}
        resp = client.patch(f"{API}/{trigger.id}", json=payload, headers=auth_headers)
        assert resp.status_code == 403


# ── DELETE /api/v1/triggers/{id} (관리자) ──


class TestDeleteTrigger:
    """트리거 삭제 테스트 (관리자 전용)"""

    def test_delete_trigger_success(
        self, client: TestClient, create_issue, create_trigger, admin_headers
    ):
        """관리자가 트리거 정상 삭제"""
        issue = create_issue()
        trigger = create_trigger(issue_id=issue.id)
        resp = client.delete(f"{API}/{trigger.id}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    def test_delete_trigger_not_found(self, client: TestClient, admin_headers):
        """존재하지 않는 트리거 삭제 404"""
        fake_id = str(uuid4())
        resp = client.delete(f"{API}/{fake_id}", headers=admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "E_RESOURCE_005"

    def test_delete_trigger_member_forbidden(
        self, client: TestClient, create_issue, create_trigger, auth_headers
    ):
        """일반 사용자가 트리거 삭제 시 403"""
        issue = create_issue()
        trigger = create_trigger(issue_id=issue.id)
        resp = client.delete(f"{API}/{trigger.id}", headers=auth_headers)
        assert resp.status_code == 403
