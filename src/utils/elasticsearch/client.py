"""Elasticsearch 클라이언트 싱글턴 및 nori 인덱스 매핑 관리."""

from __future__ import annotations

import logging
from functools import lru_cache

from elasticsearch import Elasticsearch

from src.core.config import get_settings

logger = logging.getLogger(__name__)

# nori 분석기 기반 인덱스 매핑
INDEX_SETTINGS = {
    "settings": {
        "analysis": {
            "analyzer": {
                "nori_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tok",
                    "filter": ["nori_readingform", "lowercase"],
                }
            },
            "tokenizer": {
                "nori_tok": {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed",
                }
            },
        },
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "title": {"type": "text", "analyzer": "nori_analyzer", "boost": 2.0},
            "content_text": {"type": "text", "analyzer": "nori_analyzer"},
            "source_name": {"type": "keyword"},
            "url": {"type": "keyword"},
            "published_at": {"type": "date", "ignore_malformed": True},
            "indexed_at": {"type": "date"},
        }
    },
}


@lru_cache(maxsize=1)
def get_es_client() -> Elasticsearch | None:
    """ES 클라이언트 싱글턴. URL 미설정 시 None 반환."""
    settings = get_settings()
    if not settings.elasticsearch_url:
        return None
    return Elasticsearch(
        settings.elasticsearch_url,
        request_timeout=settings.elasticsearch_timeout,
    )


def is_es_available() -> bool:
    """ES 연결 가능 여부를 ping으로 확인."""
    client = get_es_client()
    if client is None:
        return False
    try:
        return client.ping()
    except Exception:
        logger.warning("Elasticsearch ping 실패")
        return False


def ensure_index() -> bool:
    """인덱스가 없으면 nori 매핑으로 생성. 성공 시 True."""
    client = get_es_client()
    if client is None:
        return False
    settings = get_settings()
    index_name = settings.elasticsearch_index
    try:
        if not client.indices.exists(index=index_name):
            client.indices.create(index=index_name, body=INDEX_SETTINGS)
            logger.info("ES 인덱스 생성: %s", index_name)
        return True
    except Exception:
        logger.exception("ES 인덱스 생성 실패: %s", index_name)
        return False
