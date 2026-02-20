from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from trend_korea.infrastructure.db.models.news_channel import NewsChannel
from trend_korea.infrastructure.db.session import SessionLocal
from trend_korea.keyword_crawler.headline_extractor import (
    extract_headlines,
    extract_headlines_from_rss,
    get_rss_url,
)
from trend_korea.keyword_crawler.http_client import AsyncHttpClient
from trend_korea.keyword_crawler.keyword_analyzer import KeywordResult, extract_keywords

logger = logging.getLogger(__name__)

BLOCK_PATTERNS = [
    "captcha", "are you a robot", "i'm not a robot", "access denied",
    "403 forbidden", "비정상적인 접근", "접근이 제한", "자동화된 요청",
]


def _looks_blocked(html: str) -> bool:
    lower = html[:5000].lower()
    # meta robots 태그 오탐 방지: 실제 차단 페이지는 본문이 매우 짧음
    if len(html) > 20000:
        return False
    return any(p in lower for p in BLOCK_PATTERNS)


# ── 결과 데이터 ──────────────────────────────────────────────


@dataclass(slots=True)
class ChannelCrawlResult:
    channel_code: str
    channel_name: str
    channel_url: str
    category: str
    headlines: list[str]
    keywords: list[KeywordResult]
    fetch_status: str  # success | failed | blocked | timeout
    error_message: str | None = None
    fetch_duration_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class CrawlOutput:
    crawled_at: str
    total_channels: int
    successful_channels: int
    failed_channels: int
    channels: list[ChannelCrawlResult]
    aggregated_keywords: list[KeywordResult]

    def to_dict(self) -> dict:
        return asdict(self)


# ── DB 조회 ──────────────────────────────────────────────────


def load_active_channels(db: Session) -> list[NewsChannel]:
    stmt = select(NewsChannel).where(NewsChannel.is_active.is_(True)).order_by(NewsChannel.code)
    return list(db.scalars(stmt).all())


# ── 비동기 크롤링 ───────────────────────────────────────────


async def _fetch_one(
    client: AsyncHttpClient,
    channel: NewsChannel,
    top_n: int,
) -> ChannelCrawlResult:
    start = time.monotonic()
    try:
        # RSS 피드가 있으면 RSS 우선, 없으면 메인 페이지 HTML
        rss_url = get_rss_url(channel.code)
        if rss_url:
            xml = await client.get_text(rss_url)
            headlines = extract_headlines_from_rss(xml)
        else:
            html = await client.get_text(channel.url)
            if _looks_blocked(html):
                duration = int((time.monotonic() - start) * 1000)
                return ChannelCrawlResult(
                    channel_code=channel.code, channel_name=channel.name,
                    channel_url=channel.url, category=channel.category,
                    headlines=[], keywords=[], fetch_status="blocked",
                    error_message="Blocked by anti-bot", fetch_duration_ms=duration,
                )
            headlines = extract_headlines(html, channel.code)

        duration = int((time.monotonic() - start) * 1000)
        keywords = extract_keywords(headlines, top_n=top_n)

        return ChannelCrawlResult(
            channel_code=channel.code, channel_name=channel.name,
            channel_url=channel.url, category=channel.category,
            headlines=headlines, keywords=keywords,
            fetch_status="success", fetch_duration_ms=duration,
        )
    except Exception as exc:
        duration = int((time.monotonic() - start) * 1000)
        logger.warning("Crawl failed %s: %s", channel.code, exc)
        return ChannelCrawlResult(
            channel_code=channel.code, channel_name=channel.name,
            channel_url=channel.url, category=channel.category,
            headlines=[], keywords=[], fetch_status="failed",
            error_message=str(exc)[:300], fetch_duration_ms=duration,
        )


async def _crawl_async(
    channels: list[NewsChannel],
    top_n_per_channel: int,
    top_n_aggregated: int,
    timeout: float,
) -> CrawlOutput:
    client = AsyncHttpClient(timeout=timeout)
    results = await asyncio.gather(*[
        _fetch_one(client, ch, top_n_per_channel) for ch in channels
    ])

    all_headlines: list[str] = []
    for r in results:
        all_headlines.extend(r.headlines)
    aggregated = extract_keywords(all_headlines, top_n=top_n_aggregated)

    ok = sum(1 for r in results if r.fetch_status == "success")
    return CrawlOutput(
        crawled_at=datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        total_channels=len(channels),
        successful_channels=ok,
        failed_channels=len(channels) - ok,
        channels=list(results),
        aggregated_keywords=aggregated,
    )


# ── 동기 진입점 ─────────────────────────────────────────────


def run_crawl(
    top_n_per_channel: int = 20,
    top_n_aggregated: int = 30,
    timeout: float = 15.0,
    category_filter: str | None = None,
) -> CrawlOutput:
    with SessionLocal() as db:
        channels = load_active_channels(db)

    if category_filter:
        channels = [c for c in channels if c.category == category_filter]

    if not channels:
        logger.warning("No active channels found")
        return CrawlOutput(
            crawled_at=datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
            total_channels=0, successful_channels=0, failed_channels=0,
            channels=[], aggregated_keywords=[],
        )

    logger.info("Crawling %d channels...", len(channels))
    return asyncio.run(_crawl_async(channels, top_n_per_channel, top_n_aggregated, timeout))


# ── DB 저장 ──────────────────────────────────────────────────


def save_to_db(output: CrawlOutput) -> int:
    """크롤링 결과를 crawled_keywords 테이블에 저장한다. 삽입된 행 수를 반환."""
    import uuid
    from trend_korea.infrastructure.db.models.crawled_keyword import CrawledKeyword

    now = datetime.now(timezone.utc)
    raw = output.crawled_at.rstrip("Z")
    if "+" not in raw and "-" not in raw[10:]:
        raw += "+00:00"
    crawled_at = datetime.fromisoformat(raw)
    rows: list[CrawledKeyword] = []

    # 채널별 키워드
    for ch in output.channels:
        for kw in ch.keywords:
            rows.append(CrawledKeyword(
                id=str(uuid.uuid4()),
                keyword=kw.word,
                count=kw.count,
                rank=kw.rank,
                channel_code=ch.channel_code,
                channel_name=ch.channel_name,
                category=ch.category,
                source_type="channel",
                crawled_at=crawled_at,
                created_at=now,
            ))

    # 통합 키워드
    for kw in output.aggregated_keywords:
        rows.append(CrawledKeyword(
            id=str(uuid.uuid4()),
            keyword=kw.word,
            count=kw.count,
            rank=kw.rank,
            channel_code=None,
            channel_name=None,
            category=None,
            source_type="aggregated",
            crawled_at=crawled_at,
            created_at=now,
        ))

    with SessionLocal() as db:
        db.add_all(rows)
        db.commit()

    logger.info("Saved %d keyword rows to DB", len(rows))
    return len(rows)
