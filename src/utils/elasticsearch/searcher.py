"""교차 키워드 검색 — named queries로 매칭 키워드 판별."""

from __future__ import annotations

import logging

from src.core.config import get_settings
from src.utils.elasticsearch.client import get_es_client

logger = logging.getLogger(__name__)


def cross_reference_search(
    keywords: list[str],
    min_matches: int = 1,
) -> list[dict]:
    """키워드가 매칭되는 기사를 ES에서 검색한다.

    각 키워드를 named query로 등록하여 단일 쿼리로 매칭 키워드를 판별한다.

    Returns:
        기존 _cross_reference_articles와 동일한 구조의 dict 리스트.
        ES 미사용 시 빈 리스트.
    """
    client = get_es_client()
    if client is None or len(keywords) < min_matches:
        return []

    settings = get_settings()
    index_name = settings.elasticsearch_index

    # bool.should + minimum_should_match로 교차 키워드 필터링
    should_clauses = []
    for kw in keywords:
        should_clauses.append({
            "multi_match": {
                "query": kw,
                "fields": ["title^2", "content_text"],
                "type": "phrase",
                "slop": 1,
                "_name": f"kw:{kw}",
            }
        })

    query = {
        "bool": {
            "should": should_clauses,
            "minimum_should_match": min_matches,
        }
    }

    try:
        resp = client.search(
            index=index_name,
            query=query,
            size=200,
            _source=["title", "content_text", "source_name", "url", "published_at"],
        )
    except Exception:
        logger.exception("ES 교차 키워드 검색 실패")
        return []

    results: list[dict] = []
    for hit in resp["hits"]["hits"]:
        source = hit["_source"]
        # named queries에서 매칭된 키워드 추출
        matched_queries = hit.get("matched_queries", [])
        matched_keywords = [q.removeprefix("kw:") for q in matched_queries]
        kw_count = len(matched_keywords)

        if kw_count < min_matches:
            continue

        results.append({
            "title": source.get("title", ""),
            "content_text": source.get("content_text", ""),
            "source_name": source.get("source_name", ""),
            "url": source.get("url", ""),
            "published_at": source.get("published_at"),
            "keyword": ", ".join(matched_keywords),
            "matched_keywords": matched_keywords,
            "keyword_count": kw_count,
            "confidence": min(0.6 + kw_count * 0.1, 1.0),
            "es_score": hit["_score"],
        })

    results.sort(key=lambda a: (-a["keyword_count"], -a.get("es_score", 0)))
    return results
