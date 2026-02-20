from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

# ── 채널별 설정 ─────────────────────────────────────────────
# selectors : CSS 셀렉터 (메인 페이지 HTML)
# rss       : RSS 피드 URL (SPA 사이트 대체)
# use_json_ld : JSON-LD에서 헤드라인 추출

_SITE_CONFIGS: dict[str, dict] = {
    # === 방송 ===
    "yonhapnews_tv": {
        "selectors": [
            ".top-news .title a", ".news-list .title a",
            "h2.title a", ".headline-list a",
        ],
    },
    "sbs": {
        "rss": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER",
        "selectors": [],
    },
    "mbc": {
        "selectors": [
            ".news_list .title a", ".headline_news a",
            ".top_news .tit a", "h3.tit a",
        ],
        "note": "SPA - static HTML에서 콘텐츠 제한적",
    },
    "kbs": {
        "selectors": [
            ".headline-list .title a", ".news-list .title a",
            "#container .tit a", "h3.tit a",
        ],
        "note": "SPA - static HTML에서 콘텐츠 제한적",
    },
    "jtbc": {
        "selectors": [
            ".headline_list a", ".news_area .title a",
            ".main-news-list a",
        ],
        "note": "SPA - static HTML에서 콘텐츠 제한적",
    },
    # === 신문 ===
    "chosun": {
        "selectors": [
            'a[class*="story-card"]', 'h2[class*="story-card"] a',
            ".story-card__headline a", "article a",
        ],
        "use_json_ld": True,
    },
    "donga": {
        "selectors": [
            ".main_headline a", ".news_list .title a",
            "h3.title a", ".article_headline a",
        ],
    },
    "hani": {
        "selectors": [
            ".main-top .title a", ".article-title a",
            ".article-list .title a", "h4.title a",
        ],
    },
    "khan": {
        "selectors": [
            ".headline a", ".news-list .title a",
            "h3.tit a", ".main_art .tit a",
        ],
    },
    "mk": {
        "selectors": [
            ".news_list .title a", ".headline .tit a",
            "h3.news_ttl a", ".top_news a",
        ],
    },
}

_STRIP_TAGS = ["nav", "footer", "aside", "script", "style", "noscript", "header"]

_KOREAN_RE = re.compile(r"[\uAC00-\uD7AF]{2,}")


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def get_rss_url(channel_code: str) -> str | None:
    """채널에 RSS 피드 URL이 있으면 반환."""
    return _SITE_CONFIGS.get(channel_code, {}).get("rss")


def extract_headlines_from_rss(xml: str) -> list[str]:
    """RSS/XML에서 <item><title> 목록을 추출한다."""
    soup = BeautifulSoup(xml, "xml")
    headlines: list[str] = []
    seen: set[str] = set()
    for item in soup.find_all("item"):
        title_tag = item.find("title")
        if not title_tag:
            continue
        t = _compact(title_tag.get_text(strip=True))
        if t and len(t) >= 4 and t not in seen:
            seen.add(t)
            headlines.append(t)
    return headlines


def extract_headlines(html: str, channel_code: str) -> list[str]:
    """채널 메인 페이지 HTML에서 헤드라인 텍스트 목록을 추출한다."""
    soup = BeautifulSoup(html, "lxml")

    # 노이즈 영역 제거
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    headlines: list[str] = []
    seen: set[str] = set()

    def _add(text: str) -> None:
        t = _compact(text)
        if t and len(t) >= 4 and t not in seen:
            seen.add(t)
            headlines.append(t)

    config = _SITE_CONFIGS.get(channel_code, {})

    # Phase 1: 사이트별 셀렉터
    for sel in config.get("selectors", []):
        for el in soup.select(sel):
            _add(el.get_text(" ", strip=True))

    # Phase 2: JSON-LD
    if config.get("use_json_ld"):
        _extract_json_ld(soup, _add)

    # Phase 3: 제너릭 폴백 (셀렉터로 충분히 못 잡았을 때)
    if len(headlines) < 5:
        for tag_name in ["h1", "h2", "h3"]:
            for tag in soup.find_all(tag_name):
                _add(tag.get_text(" ", strip=True))

    if len(headlines) < 5:
        for a_tag in soup.find_all("a"):
            text = _compact(a_tag.get_text(" ", strip=True))
            if 8 <= len(text) <= 120 and _KOREAN_RE.search(text):
                _add(text)

    return headlines


def _extract_json_ld(soup: BeautifulSoup, add_fn) -> None:
    for script in soup.select("script[type='application/ld+json']"):
        try:
            data = json.loads(script.get_text(strip=True))
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ("headline", "name", "title"):
                val = item.get(key)
                if isinstance(val, str):
                    add_fn(val)
