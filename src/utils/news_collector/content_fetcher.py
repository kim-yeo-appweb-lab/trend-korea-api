"""매칭된 기사 URL에서 본문을 비동기 병렬 수집."""

from __future__ import annotations

import asyncio
import logging
import re

from bs4 import BeautifulSoup

from src.utils.keyword_crawler.http_client import AsyncHttpClient

logger = logging.getLogger(__name__)

_NOISE_TAGS = ["nav", "footer", "aside", "script", "style", "header", "noscript"]
_MAX_CONTENT_CHARS = 3000


def _extract_content(html: str) -> str:
    """HTML에서 기사 본문 텍스트를 추출한다."""
    soup = BeautifulSoup(html, "lxml")

    # 1) 노이즈 태그 제거
    for tag_name in _NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 2) <article> 태그 우선
    article = soup.find("article")
    if article:
        paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
        text = "\n".join(p for p in paragraphs if p)
        if len(text) >= 50:
            return text[:_MAX_CONTENT_CHARS]

    # 3) 폴백: 전체 <p> 중 50자 이상인 것만
    paragraphs = [
        p.get_text(strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) >= 50
    ]
    text = "\n".join(paragraphs)

    # 4) 최후 폴백: 연속 공백 정리 후 반환
    if not text:
        body = soup.find("body")
        if body:
            text = re.sub(r"\s+", " ", body.get_text(" ", strip=True))

    return text[:_MAX_CONTENT_CHARS]


async def _fetch_one_content(
    client: AsyncHttpClient,
    article: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    """단일 기사 URL에서 본문을 수집한다. 실패 시 content_text=""."""
    url = article.get("url", "")
    if not url:
        return article

    async with semaphore:
        try:
            html = await client.get_text(url)
            content = _extract_content(html)
            return {**article, "content_text": content}
        except Exception as exc:
            logger.debug("본문 수집 실패 %s: %s", url, exc)
            return {**article, "content_text": ""}


async def _fetch_all(
    articles: list[dict],
    max_concurrent: int,
    timeout: float,
) -> list[dict]:
    """비동기 병렬로 기사 본문을 수집한다."""
    client = AsyncHttpClient(timeout=timeout, retries=1)
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [_fetch_one_content(client, art, semaphore) for art in articles]
    return list(await asyncio.gather(*tasks))


def fetch_articles_content(
    articles: list[dict],
    max_concurrent: int = 5,
    timeout: float = 10.0,
) -> list[dict]:
    """매칭된 기사 URL에서 본문을 비동기 병렬 수집한다. (동기 진입점)"""
    if not articles:
        return []
    return asyncio.run(_fetch_all(articles, max_concurrent, timeout))
