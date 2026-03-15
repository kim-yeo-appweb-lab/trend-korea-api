from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(slots=True)
class HeadlineItem:
    """메인페이지에서 추출한 개별 헤드라인(제목 + URL)."""

    title: str
    url: str
    source_name: str
    channel_code: str

# ── 채널별 설정 ─────────────────────────────────────────────
# selectors : CSS 셀렉터 (메인 페이지 HTML)
# rss       : RSS 피드 URL (SPA 사이트 대체)
# use_json_ld : JSON-LD에서 헤드라인 추출

_SITE_CONFIGS: dict[str, dict] = {
    # === 방송 ===
    "yonhapnews_tv": {
        "selectors": [
            ".top-news .title a",
            ".news-list .title a",
            "h2.title a",
            ".headline-list a",
        ],
    },
    "sbs": {
        "rss": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER",
        "selectors": [],
    },
    "mbc": {
        "selectors": [
            ".news_list .title a",
            ".headline_news a",
            ".top_news .tit a",
            "h3.tit a",
        ],
        "note": "SPA - static HTML에서 콘텐츠 제한적",
    },
    "kbs": {
        "selectors": [
            ".headline-list .title a",
            ".news-list .title a",
            "#container .tit a",
            "h3.tit a",
        ],
        "note": "SPA - static HTML에서 콘텐츠 제한적",
    },
    "jtbc": {
        "selectors": [
            ".headline_list a",
            ".news_area .title a",
            ".main-news-list a",
        ],
        "note": "SPA - static HTML에서 콘텐츠 제한적",
    },
    # === 신문 ===
    "chosun": {
        "selectors": [
            'a[class*="story-card"]',
            'h2[class*="story-card"] a',
            ".story-card__headline a",
            "article a",
        ],
        "use_json_ld": True,
    },
    "donga": {
        "selectors": [
            ".main_headline a",
            ".news_list .title a",
            "h3.title a",
            ".article_headline a",
        ],
    },
    "hani": {
        "selectors": [
            ".main-top .title a",
            ".article-title a",
            ".article-list .title a",
            "h4.title a",
        ],
    },
    "khan": {
        "selectors": [
            ".headline a",
            ".news-list .title a",
            "h3.tit a",
            ".main_art .tit a",
        ],
    },
    "mk": {
        "selectors": [
            ".news_list .title a",
            ".headline .tit a",
            "h3.news_ttl a",
            ".top_news a",
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


def extract_headline_items_from_rss(
    xml: str,
    channel_name: str,
    channel_code: str,
) -> list[HeadlineItem]:
    """RSS/XML에서 <item>의 title + link를 추출한다."""
    soup = BeautifulSoup(xml, "xml")
    items: list[HeadlineItem] = []
    seen: set[str] = set()
    for item in soup.find_all("item"):
        title_tag = item.find("title")
        if not title_tag:
            continue
        t = _compact(title_tag.get_text(strip=True))
        if not t or len(t) < 4 or t in seen:
            continue
        seen.add(t)
        link_tag = item.find("link")
        url = ""
        if link_tag:
            url = _compact(link_tag.get_text(strip=True))
        if not url:
            continue
        items.append(HeadlineItem(title=t, url=url, source_name=channel_name, channel_code=channel_code))
    return items


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


def extract_headline_items(
    html: str,
    channel_code: str,
    channel_name: str,
    base_url: str,
) -> list[HeadlineItem]:
    """채널 메인 페이지 HTML에서 헤드라인(title + URL) 목록을 추출한다."""
    soup = BeautifulSoup(html, "lxml")

    # 노이즈 영역 제거
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    items: list[HeadlineItem] = []
    seen_titles: set[str] = set()
    seen_urls: set[str] = set()

    def _add_item(text: str, url: str) -> None:
        t = _compact(text)
        if not t or len(t) < 4 or t in seen_titles:
            return
        if url and url in seen_urls:
            return
        seen_titles.add(t)
        if url:
            seen_urls.add(url)
            items.append(
                HeadlineItem(
                    title=t, url=url, source_name=channel_name, channel_code=channel_code,
                )
            )

    config = _SITE_CONFIGS.get(channel_code, {})

    # Phase 1: 사이트별 셀렉터
    for sel in config.get("selectors", []):
        for el in soup.select(sel):
            href = el.get("href", "")
            # 셀렉터가 <a> 자체가 아닌 경우, 부모/자식에서 <a> 탐색
            if not href:
                a_tag = el.find("a") if el.name != "a" else el
                if a_tag and a_tag.name == "a":
                    href = a_tag.get("href", "")
                if not href and el.parent and el.parent.name == "a":
                    href = el.parent.get("href", "")
            url = urljoin(base_url, href) if href else ""
            _add_item(el.get_text(" ", strip=True), url)

    # Phase 2: JSON-LD (URL 없이 제목만 — 하위 호환)
    if config.get("use_json_ld"):
        _extract_json_ld_items(soup, channel_name, channel_code, _add_item)

    # Phase 3: 제너릭 폴백
    if len(items) < 5:
        for tag_name in ["h1", "h2", "h3"]:
            for tag in soup.find_all(tag_name):
                a_child = tag.find("a")
                if a_child:
                    href = a_child.get("href", "")
                    url = urljoin(base_url, href) if href else ""
                    _add_item(tag.get_text(" ", strip=True), url)
                else:
                    _add_item(tag.get_text(" ", strip=True), "")

    if len(items) < 5:
        for a_tag in soup.find_all("a"):
            text = _compact(a_tag.get_text(" ", strip=True))
            if 8 <= len(text) <= 120 and _KOREAN_RE.search(text):
                href = a_tag.get("href", "")
                url = urljoin(base_url, href) if href else ""
                _add_item(text, url)

    return items


def extract_headlines(html: str, channel_code: str) -> list[str]:
    """채널 메인 페이지 HTML에서 헤드라인 텍스트 목록을 추출한다."""
    soup = BeautifulSoup(html, "lxml")

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

    for sel in config.get("selectors", []):
        for el in soup.select(sel):
            _add(el.get_text(" ", strip=True))

    if config.get("use_json_ld"):
        _extract_json_ld(soup, _add)

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


def _extract_json_ld_items(
    soup: BeautifulSoup,
    channel_name: str,
    channel_code: str,
    add_item_fn,
) -> None:
    """JSON-LD에서 title + url을 추출하여 add_item_fn(title, url) 호출."""
    for script in soup.select("script[type='application/ld+json']"):
        try:
            data = json.loads(script.get_text(strip=True))
        except Exception:
            continue
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            title = ""
            for key in ("headline", "name", "title"):
                val = entry.get(key)
                if isinstance(val, str):
                    title = val
                    break
            url = entry.get("url", "")
            if title:
                add_item_fn(title, url if isinstance(url, str) else "")
