# 사건(Event) 도메인 API 테스트

from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from trend_korea.db.enums import Importance, SourceEntityType

API = "/api/v1/events"


# ── GET /api/v1/events ──


class TestListEvents:
    """사건 목록 조회 테스트"""

    def test_list_events_empty(self, client: TestClient):
        """데이터 없을 때 빈 목록 반환"""
        resp = client.get(API)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["items"] == []

    def test_list_events_with_data(self, client: TestClient, create_event):
        """데이터가 있을 때 목록 반환"""
        create_event(title="사건1")
        create_event(title="사건2")
        resp = client.get(API)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]["items"]) == 2

    def test_list_events_filter_importance(self, client: TestClient, create_event):
        """중요도 필터링"""
        create_event(title="높은 사건", importance=Importance.HIGH)
        create_event(title="낮은 사건", importance=Importance.LOW)
        resp = client.get(API, params={"importance": "high"})
        assert resp.status_code == 200
        body = resp.json()
        items = body["data"]["items"]
        assert len(items) == 1
        assert items[0]["importance"] == "high"

    def test_list_events_pagination(self, client: TestClient, create_event):
        """페이지네이션: limit으로 조회 수 제한"""
        for i in range(5):
            create_event(title=f"사건{i}")
        resp = client.get(API, params={"limit": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]["items"]) == 2
        assert body["data"]["cursor"]["hasMore"] is True
        assert body["data"]["cursor"]["next"] is not None


# ── GET /api/v1/events/{id} ──


class TestGetEvent:
    """사건 상세 조회 테스트"""

    def test_get_event_success(self, client: TestClient, create_event):
        """존재하는 사건 상세 조회"""
        event = create_event(title="상세 조회 사건")
        resp = client.get(f"{API}/{event.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == event.id
        assert body["data"]["title"] == "상세 조회 사건"

    def test_get_event_not_found(self, client: TestClient):
        """존재하지 않는 사건 404 반환"""
        fake_id = str(uuid4())
        resp = client.get(f"{API}/{fake_id}")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "E_RESOURCE_001"


# ── POST /api/v1/events/{id}/save ──


class TestSaveEvent:
    """사건 저장 테스트"""

    def test_save_event_success(self, client: TestClient, create_event, auth_headers):
        """정상 사건 저장"""
        event = create_event()
        resp = client.post(f"{API}/{event.id}/save", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["eventId"] == event.id
        assert body["data"]["isSaved"] is True

    def test_save_event_already_saved(self, client: TestClient, create_event, auth_headers):
        """이미 저장된 사건 409 반환"""
        event = create_event()
        client.post(f"{API}/{event.id}/save", headers=auth_headers)
        resp = client.post(f"{API}/{event.id}/save", headers=auth_headers)
        assert resp.status_code == 409
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "E_CONFLICT_003"

    def test_save_event_not_found(self, client: TestClient, auth_headers):
        """존재하지 않는 사건 저장 시도 404"""
        fake_id = str(uuid4())
        resp = client.post(f"{API}/{fake_id}/save", headers=auth_headers)
        assert resp.status_code == 404

    def test_save_event_no_token(self, client: TestClient, create_event):
        """토큰 없이 저장 시도 401"""
        event = create_event()
        resp = client.post(f"{API}/{event.id}/save")
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False


# ── DELETE /api/v1/events/{id}/save ──


class TestUnsaveEvent:
    """사건 저장 해제 테스트"""

    def test_unsave_event_success(self, client: TestClient, create_event, auth_headers):
        """정상 사건 저장 해제"""
        event = create_event()
        client.post(f"{API}/{event.id}/save", headers=auth_headers)
        resp = client.delete(f"{API}/{event.id}/save", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    def test_unsave_event_not_found(self, client: TestClient, auth_headers):
        """존재하지 않는 사건 저장 해제 404"""
        fake_id = str(uuid4())
        resp = client.delete(f"{API}/{fake_id}/save", headers=auth_headers)
        assert resp.status_code == 404

    def test_unsave_event_no_token(self, client: TestClient, create_event):
        """토큰 없이 저장 해제 시도 401"""
        event = create_event()
        resp = client.delete(f"{API}/{event.id}/save")
        assert resp.status_code == 401


# ── POST /api/v1/events (관리자) ──


class TestCreateEvent:
    """사건 생성 테스트 (관리자 전용)"""

    @pytest.fixture()
    def _source(self, create_source):
        """테스트용 출처 생성"""
        return create_source()

    def test_create_event_success(self, client: TestClient, admin_headers, _source):
        """관리자가 사건 정상 생성 201"""
        payload = {
            "occurredAt": "2025-06-15T09:00:00Z",
            "title": "새 사건",
            "summary": "새 사건 요약입니다.",
            "importance": "high",
            "verificationStatus": "unverified",
            "tagIds": [],
            "sourceIds": [_source.id],
        }
        resp = client.post(API, json=payload, headers=admin_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["title"] == "새 사건"
        assert body["data"]["importance"] == "high"

    def test_create_event_missing_fields(self, client: TestClient, admin_headers):
        """필수 필드 누락 시 400 반환"""
        payload = {"title": "제목만"}
        resp = client.post(API, json=payload, headers=admin_headers)
        assert resp.status_code == 400

    def test_create_event_member_forbidden(self, client: TestClient, auth_headers, _source):
        """일반 사용자가 사건 생성 시 403"""
        payload = {
            "occurredAt": "2025-06-15T09:00:00Z",
            "title": "일반 사용자 사건",
            "summary": "요약",
            "importance": "low",
            "verificationStatus": "unverified",
            "tagIds": [],
            "sourceIds": [_source.id],
        }
        resp = client.post(API, json=payload, headers=auth_headers)
        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "E_PERM_002"

    def test_create_event_no_token(self, client: TestClient, _source):
        """토큰 없이 사건 생성 시 401"""
        payload = {
            "occurredAt": "2025-06-15T09:00:00Z",
            "title": "토큰 없는 사건",
            "summary": "요약",
            "importance": "low",
            "verificationStatus": "unverified",
            "tagIds": [],
            "sourceIds": [_source.id],
        }
        resp = client.post(API, json=payload)
        assert resp.status_code == 401


# ── PATCH /api/v1/events/{id} (관리자) ──


class TestUpdateEvent:
    """사건 수정 테스트 (관리자 전용)"""

    def test_update_event_success(self, client: TestClient, create_event, admin_headers):
        """관리자가 사건 정상 수정"""
        event = create_event(title="수정 전 제목")
        payload = {"title": "수정 후 제목"}
        resp = client.patch(f"{API}/{event.id}", json=payload, headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["title"] == "수정 후 제목"

    def test_update_event_not_found(self, client: TestClient, admin_headers):
        """존재하지 않는 사건 수정 404"""
        fake_id = str(uuid4())
        payload = {"title": "수정 시도"}
        resp = client.patch(f"{API}/{fake_id}", json=payload, headers=admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "E_RESOURCE_001"

    def test_update_event_member_forbidden(self, client: TestClient, create_event, auth_headers):
        """일반 사용자가 사건 수정 시 403"""
        event = create_event()
        payload = {"title": "일반 사용자 수정"}
        resp = client.patch(f"{API}/{event.id}", json=payload, headers=auth_headers)
        assert resp.status_code == 403


# ── DELETE /api/v1/events/{id} (관리자) ──


class TestDeleteEvent:
    """사건 삭제 테스트 (관리자 전용)"""

    def test_delete_event_success(self, client: TestClient, create_event, admin_headers):
        """관리자가 사건 정상 삭제"""
        event = create_event()
        resp = client.delete(f"{API}/{event.id}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        # 삭제 후 조회 시 404
        resp2 = client.get(f"{API}/{event.id}")
        assert resp2.status_code == 404

    def test_delete_event_not_found(self, client: TestClient, admin_headers):
        """존재하지 않는 사건 삭제 404"""
        fake_id = str(uuid4())
        resp = client.delete(f"{API}/{fake_id}", headers=admin_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "E_RESOURCE_001"

    def test_delete_event_member_forbidden(self, client: TestClient, create_event, auth_headers):
        """일반 사용자가 사건 삭제 시 403"""
        event = create_event()
        resp = client.delete(f"{API}/{event.id}", headers=auth_headers)
        assert resp.status_code == 403
