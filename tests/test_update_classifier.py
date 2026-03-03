"""update_classifier 단위 테스트 — DB 없이 순수 함수 테스트."""

from src.utils.pipeline.update_classifier import (
    compute_semantic_hash,
    compute_title_hash,
    normalize_article,
    normalize_keywords,
    normalize_url,
)


# ── URL 정규화 ──


class TestNormalizeUrl:
    def test_removes_tracking_params(self):
        url = "https://example.com/news?utm_source=twitter&id=123"
        result = normalize_url(url)
        assert "utm_source" not in result
        assert "id=123" in result

    def test_removes_www_prefix(self):
        url = "https://www.example.com/news"
        result = normalize_url(url)
        assert result == "https://example.com/news"

    def test_lowercases_host(self):
        url = "https://Example.COM/News"
        result = normalize_url(url)
        assert "example.com" in result

    def test_strips_trailing_slash(self):
        url = "https://example.com/news/"
        result = normalize_url(url)
        assert result.endswith("/news")

    def test_preserves_meaningful_query(self):
        url = "https://example.com/news?id=123&page=2"
        result = normalize_url(url)
        assert "id=" in result
        assert "page=" in result

    def test_deterministic(self):
        url = "https://www.Example.com/news/?utm_source=x&id=1"
        assert normalize_url(url) == normalize_url(url)

    def test_empty_path_becomes_root(self):
        url = "https://example.com"
        result = normalize_url(url)
        assert result == "https://example.com/"


# ── 해시 결정성 ──


class TestHashes:
    def test_title_hash_deterministic(self):
        title = "테스트 기사 제목"
        assert compute_title_hash(title) == compute_title_hash(title)

    def test_title_hash_ignores_whitespace(self):
        assert compute_title_hash("테스트  기사") == compute_title_hash("테스트 기사")

    def test_title_hash_case_insensitive(self):
        assert compute_title_hash("Test Article") == compute_title_hash("test article")

    def test_semantic_hash_deterministic(self):
        h = compute_semantic_hash("제목", "본문 내용")
        assert h == compute_semantic_hash("제목", "본문 내용")

    def test_semantic_hash_different_content(self):
        h1 = compute_semantic_hash("제목", "본문A")
        h2 = compute_semantic_hash("제목", "본문B")
        assert h1 != h2

    def test_semantic_hash_none_content(self):
        h = compute_semantic_hash("제목", None)
        assert isinstance(h, str) and len(h) == 64

    def test_semantic_hash_truncates_content(self):
        long_content = "가" * 500
        h1 = compute_semantic_hash("제목", long_content)
        h2 = compute_semantic_hash("제목", long_content[:200])
        assert h1 == h2


# ── 키워드 정규화 ──


class TestNormalizeKeywords:
    def test_deduplicates(self):
        result = normalize_keywords(["AI", "ai", "AI"])
        assert result == ["ai"]

    def test_strips_whitespace(self):
        result = normalize_keywords(["  반도체  ", "반도체"])
        assert result == ["반도체"]

    def test_empty_list(self):
        assert normalize_keywords([]) == []
        assert normalize_keywords(None) == []

    def test_preserves_order(self):
        result = normalize_keywords(["반도체", "AI", "경제"])
        assert result == ["반도체", "ai", "경제"]


# ── 기사 정규화 ──


class TestNormalizeArticle:
    def test_basic_normalization(self):
        article = {
            "url": "https://www.example.com/news?utm_source=x",
            "title": "테스트 기사",
            "content": "본문 내용",
            "keywords": ["AI", "반도체"],
        }
        result = normalize_article(article)
        assert result["canonical_url"] == "https://example.com/news"
        assert result["title"] == "테스트 기사"
        assert result["content_text"] == "본문 내용"
        assert "ai" in result["normalized_keywords"]
        assert len(result["title_hash"]) == 64
        assert len(result["semantic_hash"]) == 64

    def test_naver_article_format(self):
        article = {
            "original_link": "https://news.example.com/article/123",
            "title": "네이버 기사",
            "description": "기사 설명",
            "keyword": "반도체",
        }
        result = normalize_article(article)
        assert "news.example.com" in result["canonical_url"]
        assert result["normalized_keywords"] == ["반도체"]

    def test_string_keywords(self):
        article = {
            "url": "https://example.com",
            "title": "기사",
            "keywords": "AI, 반도체, 경제",
        }
        result = normalize_article(article)
        assert "ai" in result["normalized_keywords"]
        assert "반도체" in result["normalized_keywords"]
