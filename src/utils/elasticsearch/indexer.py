"""뉴스 기사 벌크 인덱싱."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from elasticsearch.helpers import bulk

from src.core.config import get_settings
from src.utils.elasticsearch.client import ensure_index, get_es_client

logger = logging.getLogger(__name__)


def bulk_index_articles(articles: list[dict]) -> int:
    """기사 목록을 ES에 벌크 인덱싱한다. URL을 _id로 사용하여 자연 중복 제거.

    Returns:
        인덱싱 성공 건수. ES 미사용 시 0.
    """
    client = get_es_client()
    if client is None or not articles:
        return 0

    if not ensure_index():
        return 0

    settings = get_settings()
    index_name = settings.elasticsearch_index
    now = datetime.now(timezone.utc).isoformat()

    actions = []
    for art in articles:
        url = art.get("url") or art.get("original_link") or art.get("link", "")
        if not url:
            continue
        actions.append({
            "_index": index_name,
            "_id": url,
            "_source": {
                "title": art.get("title", ""),
                "content_text": art.get("content_text", ""),
                "source_name": art.get("source_name", ""),
                "url": url,
                "published_at": art.get("published_at"),
                "indexed_at": now,
            },
        })

    if not actions:
        return 0

    try:
        success, errors = bulk(client, actions, raise_on_error=False)
        if errors:
            logger.warning("ES 벌크 인덱싱 일부 실패: %d건", len(errors))
        return success
    except Exception:
        logger.exception("ES 벌크 인덱싱 실패")
        return 0
