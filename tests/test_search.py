"""search 도메인 테스트"""

from starlette.testclient import TestClient


# ── GET /api/v1/search ──


def test_search_빈결과(client: TestClient):
    """검색 결과가 없으면 빈 목록 반환"""
    resp = client.get("/api/v1/search", params={"q": "존재하지않는키워드xyz"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []
    assert body["data"]["pagination"]["totalItems"] == 0


def test_search_검색어일치(client: TestClient, create_event, create_issue, member_user, create_post):
    """검색어와 일치하는 사건, 이슈, 게시글이 검색됨"""
    create_event(title="대한민국 경제 위기", summary="경제 관련 사건")
    create_issue(title="대한민국 정치 이슈", description="정치 관련 이슈")
    create_post(author_id=member_user["user"].id, title="대한민국 사회 이야기", content="사회 이야기")

    resp = client.get("/api/v1/search", params={"q": "대한민국"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) >= 3

    # 각 타입이 모두 포함되는지 확인
    types = {item["type"] for item in items}
    assert "event" in types
    assert "issue" in types
    assert "post" in types


def test_search_탭필터링_events(client: TestClient, create_event, create_issue):
    """tab=events로 사건만 검색"""
    create_event(title="필터링 테스트 사건", summary="사건 요약")
    create_issue(title="필터링 테스트 이슈", description="이슈 설명")

    resp = client.get("/api/v1/search", params={"q": "필터링 테스트", "tab": "events"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    # events 탭이므로 event 타입만 포함
    for item in items:
        assert item["type"] == "event"


def test_search_탭필터링_issues(client: TestClient, create_event, create_issue):
    """tab=issues로 이슈만 검색"""
    create_event(title="이슈탭 테스트 사건", summary="사건 요약")
    create_issue(title="이슈탭 테스트 이슈", description="이슈 설명")

    resp = client.get("/api/v1/search", params={"q": "이슈탭 테스트", "tab": "issues"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    for item in items:
        assert item["type"] == "issue"


def test_search_탭필터링_community(client: TestClient, member_user, create_post, create_event):
    """tab=community로 게시글만 검색"""
    create_event(title="커뮤니티탭 사건", summary="사건 요약")
    create_post(author_id=member_user["user"].id, title="커뮤니티탭 게시글", content="게시글 내용")

    resp = client.get("/api/v1/search", params={"q": "커뮤니티탭", "tab": "community"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    for item in items:
        assert item["type"] == "post"


# ── GET /api/v1/search/events ──


def test_search_events_빈결과(client: TestClient):
    """사건 검색 결과가 없으면 빈 목록"""
    resp = client.get("/api/v1/search/events", params={"q": "없는사건abc"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []


def test_search_events_검색성공(client: TestClient, create_event):
    """사건 전용 검색 엔드포인트에서 사건만 반환"""
    create_event(title="특정 사건 검색 테스트", summary="요약")

    resp = client.get("/api/v1/search/events", params={"q": "특정 사건 검색"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) >= 1
    assert all(item["type"] == "event" for item in items)
    assert any("특정 사건 검색" in item["title"] for item in items)


# ── GET /api/v1/search/issues ──


def test_search_issues_빈결과(client: TestClient):
    """이슈 검색 결과가 없으면 빈 목록"""
    resp = client.get("/api/v1/search/issues", params={"q": "없는이슈abc"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []


def test_search_issues_검색성공(client: TestClient, create_issue):
    """이슈 전용 검색 엔드포인트에서 이슈만 반환"""
    create_issue(title="특정 이슈 검색 테스트", description="설명")

    resp = client.get("/api/v1/search/issues", params={"q": "특정 이슈 검색"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) >= 1
    assert all(item["type"] == "issue" for item in items)
    assert any("특정 이슈 검색" in item["title"] for item in items)


# ── GET /api/v1/search/posts ──


def test_search_posts_빈결과(client: TestClient):
    """게시글 검색 결과가 없으면 빈 목록"""
    resp = client.get("/api/v1/search/posts", params={"q": "없는게시글abc"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []


def test_search_posts_검색성공(client: TestClient, member_user, create_post):
    """게시글 전용 검색 엔드포인트에서 게시글만 반환"""
    create_post(
        author_id=member_user["user"].id,
        title="특정 게시글 검색 테스트",
        content="게시글 검색용 내용",
    )

    resp = client.get("/api/v1/search/posts", params={"q": "특정 게시글 검색"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) >= 1
    assert all(item["type"] == "post" for item in items)
    assert any("특정 게시글 검색" in item["title"] for item in items)
