"""네이버 뉴스 검색 API 수집기.

API: https://openapi.naver.com/v1/search/news.json
인증: X-Naver-Client-Id / X-Naver-Client-Secret 헤더
페이지네이션: start (1-based) + display (최대 100), start 상한 1000
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import httpx

from src.core.config import get_settings
from src.db.session import SessionLocal

logger = logging.getLogger(__name__)

NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"

# HTML 태그 제거 (네이버 API 응답의 <b> 등)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    return _TAG_RE.sub("", text).strip()


# ── 결과 데이터 ──────────────────────────────────────────────


@dataclass(slots=True)
class NewsItem:
    keyword: str
    title: str
    original_link: str
    naver_link: str
    description: str
    pub_date: str
    display_order: int = 0
    raw_data: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class FetchResult:
    fetched_at: str
    keywords: list[str] = field(default_factory=list)
    total_articles: int = 0
    elapsed_seconds: float = 0.0
    articles: list[NewsItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── API 호출 ──────────────────────────────────────────────────


def fetch_news(
    keyword: str,
    display: int = 100,
    max_start: int = 1000,
    sort: str = "date",
    timeout: float = 10.0,
) -> list[NewsItem]:
    """키워드로 네이버 뉴스를 검색한다.

    Args:
        keyword: 검색 키워드
        display: 페이지당 건수 (최대 100)
        max_start: 최대 start 값 (네이버 API 상한 1000)
        sort: 정렬 방식 (date=날짜순, sim=정확도순)
        timeout: HTTP 타임아웃
    """
    settings = get_settings()
    if not settings.naver_api_client or not settings.naver_api_client_secret:
        raise RuntimeError("NAVER_API_CLIENT / NAVER_API_CLIENT_SECRET 환경변수를 설정하세요")

    headers = {
        "X-Naver-Client-Id": settings.naver_api_client,
        "X-Naver-Client-Secret": settings.naver_api_client_secret,
    }

    articles: list[NewsItem] = []
    start = 1
    display = min(display, 100)  # API 상한

    with httpx.Client(timeout=timeout) as client:
        while start <= max_start:
            params = {
                "query": keyword,
                "display": str(display),
                "start": str(start),
                "sort": sort,
            }
            logger.info("뉴스 검색 keyword=%r start=%d display=%d", keyword, start, display)
            resp = client.get(NAVER_NEWS_URL, headers=headers, params=params)

            if resp.status_code != 200:
                error_body = resp.text[:300]
                logger.error("API 오류 %d: %s", resp.status_code, error_body)
                raise ValueError(f"네이버 API 오류: [{resp.status_code}] {error_body}")

            data = resp.json()
            items = data.get("items", [])
            total = data.get("total", 0)

            for i, item in enumerate(items):
                articles.append(
                    NewsItem(
                        keyword=keyword,
                        title=_strip_html(item.get("title")),
                        original_link=item.get("originallink", ""),
                        naver_link=item.get("link", ""),
                        description=_strip_html(item.get("description")),
                        pub_date=item.get("pubDate", ""),
                        display_order=start + i,
                        raw_data=json.dumps(item, ensure_ascii=False),
                    )
                )

            if not items or start + display > min(total, max_start):
                break
            start += display

    logger.info("뉴스 검색 완료 keyword=%r: %d건 (total=%d)", keyword, len(articles), total)
    return articles


# ── 메인 진입점 ───────────────────────────────────────────────


def run_fetch(
    keywords: list[str],
    display: int = 100,
    max_start: int = 1000,
    sort: str = "date",
    timeout: float = 10.0,
) -> FetchResult:
    """여러 키워드에 대해 뉴스를 순차 수집한다."""
    start_time = time.monotonic()
    now_str = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"

    all_articles: list[NewsItem] = []
    for i, kw in enumerate(keywords):
        logger.info("키워드 수집 [%d/%d] %r", i + 1, len(keywords), kw)
        try:
            news = fetch_news(kw, display=display, max_start=max_start, sort=sort, timeout=timeout)
            all_articles.extend(news)
        except Exception as exc:
            logger.warning("키워드 수집 실패 %r: %s", kw, exc)

    elapsed = time.monotonic() - start_time
    logger.info(
        "전체 수집 완료: %d개 키워드, %d건 (%.1f초)", len(keywords), len(all_articles), elapsed
    )

    return FetchResult(
        fetched_at=now_str,
        keywords=keywords,
        total_articles=len(all_articles),
        elapsed_seconds=round(elapsed, 2),
        articles=all_articles,
    )


# ── DB 저장 ──────────────────────────────────────────────────


def save_to_db(result: FetchResult) -> int:
    """수집 결과를 DB에 저장한다. 삽입된 행 수를 반환."""
    from src.db.naver_news import NaverNewsArticle

    now = datetime.now(timezone.utc)
    rows: list[NaverNewsArticle] = []

    for a in result.articles:
        rows.append(
            NaverNewsArticle(
                id=str(uuid.uuid4()),
                keyword=a.keyword,
                title=a.title,
                original_link=a.original_link,
                naver_link=a.naver_link,
                description=a.description,
                pub_date=a.pub_date,
                display_order=a.display_order,
                raw_data=a.raw_data,
                fetched_at=now,
                created_at=now,
            )
        )

    if rows:
        with SessionLocal() as db:
            db.add_all(rows)
            db.commit()
        logger.info("뉴스 %d건 DB 저장 완료", len(rows))

    return len(rows)


def to_article_dicts(result: FetchResult, limit_per_keyword: int = 3) -> list[dict]:
    """FetchResult를 파이프라인 요약기가 기대하는 기사 dict 목록으로 변환한다.

    요약기 기대 형식: {"keyword", "title", "content_text", "channel", "url", "confidence"}
    """
    # 키워드별 상위 N건만 선택
    per_kw: dict[str, list[NewsItem]] = {}
    for a in result.articles:
        per_kw.setdefault(a.keyword, []).append(a)

    articles: list[dict] = []
    for kw, items in per_kw.items():
        for item in items[:limit_per_keyword]:
            articles.append({
                "keyword": item.keyword,
                "title": item.title,
                "content_text": item.description,  # 네이버 API 요약문을 본문 대용
                "channel": "naver_news",
                "url": item.original_link or item.naver_link,
                "confidence": 0.8,  # 네이버 검색 결과 기본 신뢰도
            })
    return articles
