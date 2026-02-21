# 홈 도메인 API 테스트


class TestBreakingNews:
    """GET /api/v1/home/breaking-news 테스트"""

    def test_breaking_news_empty(self, client):
        """데이터 없을 때 빈 목록 반환"""
        res = client.get("/api/v1/home/breaking-news")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_breaking_news_with_data(self, client, create_event):
        """사건 데이터가 있으면 속보 목록 반환"""
        create_event(title="속보 사건 1")
        create_event(title="속보 사건 2")
        res = client.get("/api/v1/home/breaking-news")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        item = body["data"][0]
        assert "id" in item
        assert "title" in item
        assert "time" in item
        assert "importance" in item

    def test_breaking_news_limit(self, client, create_event):
        """limit 파라미터로 조회 개수 제한"""
        for i in range(5):
            create_event(title=f"사건 {i}")
        res = client.get("/api/v1/home/breaking-news", params={"limit": 2})
        assert res.status_code == 200
        assert len(res.json()["data"]) == 2


class TestHotPosts:
    """GET /api/v1/home/hot-posts 테스트"""

    def test_hot_posts_empty(self, client):
        """데이터 없을 때 빈 목록 반환"""
        res = client.get("/api/v1/home/hot-posts")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_hot_posts_with_data(self, client, create_post, member_user):
        """게시글 데이터가 있으면 인기 게시글 목록 반환"""
        user = member_user["user"]
        create_post(author_id=user.id, title="인기글 1")
        create_post(author_id=user.id, title="인기글 2")
        res = client.get("/api/v1/home/hot-posts")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        item = body["data"][0]
        assert "id" in item
        assert "title" in item
        assert "commentCount" in item
        assert "isHot" in item


class TestSearchRankings:
    """GET /api/v1/home/search-rankings 테스트"""

    def test_search_rankings_empty(self, client):
        """데이터 없을 때 빈 목록 반환"""
        res = client.get("/api/v1/home/search-rankings")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_search_rankings_with_data(self, client, db_session):
        """검색 랭킹 데이터가 있으면 목록 반환"""
        from datetime import datetime, timezone
        from uuid import uuid4

        from src.models.search import SearchRanking

        for i in range(3):
            ranking = SearchRanking(
                id=str(uuid4()),
                keyword=f"키워드{i}",
                rank=i + 1,
                score=100 - i * 10,
                calculated_at=datetime.now(timezone.utc),
            )
            db_session.add(ranking)
        db_session.flush()

        res = client.get("/api/v1/home/search-rankings")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) == 3
        item = body["data"][0]
        assert "rank" in item
        assert "keyword" in item
        assert "count" in item


class TestTrending:
    """GET /api/v1/home/trending 테스트"""

    def test_trending_empty(self, client):
        """데이터 없을 때 빈 목록 반환"""
        res = client.get("/api/v1/home/trending")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_trending_with_data(self, client, create_event):
        """사건 데이터가 있으면 트렌딩 목록 반환"""
        create_event(title="트렌딩 사건")
        res = client.get("/api/v1/home/trending")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        item = body["data"][0]
        assert "rank" in item
        assert "issue" in item
        assert "id" in item["issue"]
        assert "title" in item["issue"]


class TestTimelineMinimap:
    """GET /api/v1/home/timeline-minimap 테스트"""

    def test_timeline_minimap_empty(self, client):
        """데이터 없을 때 빈 dates 배열 반환"""
        res = client.get("/api/v1/home/timeline-minimap")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["dates"] == []

    def test_timeline_minimap_with_data(self, client, create_event):
        """사건 데이터가 있으면 타임라인 미니맵 반환"""
        create_event(title="타임라인 사건")
        res = client.get("/api/v1/home/timeline-minimap")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        dates = body["data"]["dates"]
        assert len(dates) == 1
        assert "date" in dates[0]
        assert "eventCount" in dates[0]
        assert "density" in dates[0]


class TestFeaturedNews:
    """GET /api/v1/home/featured-news 테스트"""

    def test_featured_news_empty(self, client):
        """데이터 없을 때 빈 목록 반환"""
        res = client.get("/api/v1/home/featured-news")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_featured_news_with_data(self, client, create_event):
        """사건 데이터가 있으면 주요 뉴스 목록 반환"""
        create_event(title="주요 뉴스 사건", summary="주요 뉴스 요약")
        res = client.get("/api/v1/home/featured-news")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        item = body["data"][0]
        assert "id" in item
        assert "title" in item
        assert "summary" in item
        assert "createdAt" in item


class TestCommunityMedia:
    """GET /api/v1/home/community-media 테스트"""

    def test_community_media_empty(self, client):
        """데이터 없을 때 빈 목록 반환"""
        res = client.get("/api/v1/home/community-media")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_community_media_with_data(self, client, create_post, member_user):
        """게시글 데이터가 있으면 커뮤니티 미디어 목록 반환"""
        user = member_user["user"]
        create_post(author_id=user.id, title="미디어 게시글")
        res = client.get("/api/v1/home/community-media")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        item = body["data"][0]
        assert "id" in item
        assert "title" in item
        assert "createdAt" in item
