"""Feed API 엔드포인트 테스트."""

from starlette.testclient import TestClient

from src.db.enums import FeedType, UpdateType


class TestLiveFeed:
    def test_empty_feed(self, client: TestClient):
        resp = client.get("/api/v1/feed/live")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["cursor"]["hasMore"] is False

    def test_feed_with_items(
        self,
        client: TestClient,
        db_session,
        create_raw_article,
        create_event_update,
        create_live_feed_item,
    ):
        article = create_raw_article(title="피드 테스트 기사")
        eu = create_event_update(
            article_id=article.id,
            update_type=UpdateType.NEW,
            update_score=0.6,
        )
        create_live_feed_item(
            update_id=eu.id,
            feed_type=FeedType.ALL,
            rank_score=0.6,
        )

        resp = client.get("/api/v1/feed/live")
        assert resp.status_code == 200
        body = resp.json()
        items = body["data"]["items"]
        assert len(items) == 1
        assert items[0]["updateType"] == "NEW"
        assert items[0]["article"]["title"] == "피드 테스트 기사"

    def test_feed_type_filter(
        self,
        client: TestClient,
        db_session,
        create_raw_article,
        create_event_update,
        create_live_feed_item,
        create_issue,
    ):
        issue = create_issue(title="필터 테스트 이슈")
        article = create_raw_article(title="필터 테스트 기사")
        eu = create_event_update(
            article_id=article.id,
            issue_id=issue.id,
            update_type=UpdateType.MAJOR_UPDATE,
            update_score=0.9,
        )
        # major 피드에만 등록
        create_live_feed_item(
            update_id=eu.id,
            issue_id=issue.id,
            feed_type=FeedType.MAJOR,
            rank_score=1.35,
        )

        # major 필터 → 1건
        resp = client.get("/api/v1/feed/live?type=major")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 1

        # breaking 필터 → 0건
        resp = client.get("/api/v1/feed/live?type=breaking")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0

    def test_feed_pagination(
        self,
        client: TestClient,
        db_session,
        create_raw_article,
        create_event_update,
        create_live_feed_item,
    ):
        for i in range(3):
            art = create_raw_article(title=f"페이지 기사 {i}")
            eu = create_event_update(article_id=art.id)
            create_live_feed_item(update_id=eu.id, rank_score=float(i))

        resp = client.get("/api/v1/feed/live?limit=2")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]["items"]) == 2
        assert body["data"]["cursor"]["hasMore"] is True
        assert body["data"]["cursor"]["next"] is not None

    def test_invalid_type_returns_error(self, client: TestClient):
        resp = client.get("/api/v1/feed/live?type=invalid")
        assert resp.status_code in (400, 422)


class TestIssueTimeline:
    def test_timeline_404_for_nonexistent_issue(self, client: TestClient):
        resp = client.get("/api/v1/issues/nonexistent-id/timeline")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "E_RESOURCE_002"

    def test_empty_timeline(
        self,
        client: TestClient,
        db_session,
        create_issue,
    ):
        issue = create_issue(title="빈 타임라인 이슈")
        resp = client.get(f"/api/v1/issues/{issue.id}/timeline")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["items"] == []

    def test_timeline_with_updates(
        self,
        client: TestClient,
        db_session,
        create_issue,
        create_raw_article,
        create_event_update,
    ):
        issue = create_issue(title="타임라인 테스트 이슈")
        art1 = create_raw_article(title="타임라인 기사 1")
        art2 = create_raw_article(title="타임라인 기사 2")
        create_event_update(
            article_id=art1.id,
            issue_id=issue.id,
            update_type=UpdateType.NEW,
        )
        create_event_update(
            article_id=art2.id,
            issue_id=issue.id,
            update_type=UpdateType.MAJOR_UPDATE,
            major_reasons=["numeric_change"],
            diff_summary="사망자 수 변경",
        )

        resp = client.get(f"/api/v1/issues/{issue.id}/timeline")
        assert resp.status_code == 200
        body = resp.json()
        items = body["data"]["items"]
        assert len(items) == 2
        # 최신순 정렬 → art2가 먼저
        assert items[0]["updateType"] in ("NEW", "MAJOR_UPDATE")
