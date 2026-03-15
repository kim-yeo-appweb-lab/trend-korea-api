"""파이프라인 수집 모델.

테이블 구조:
  crawled_keywords      — 채널별/통합 키워드 수집 결과
  keyword_intersections — 채널 간 교집합 키워드
  raw_articles          — 수집된 뉴스 기사 (URL 정규화 + 해시 기반 중복 제거)
  naver_news_articles   — 네이버 뉴스 검색 API 수집 기사
  product_info          — 한국소비자원 상품 마스터 정보
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class CrawledKeyword(Base):
    __tablename__ = "crawled_keywords"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    channel_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    channel_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class KeywordIntersection(Base):
    __tablename__ = "keyword_intersections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel_count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    channel_codes: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    min_channels: Mapped[int] = mapped_column(Integer, nullable=False)
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RawArticle(Base):
    """수집된 뉴스 기사. URL 정규화 및 해시 기반 중복 제거 대상."""

    __tablename__ = "raw_articles"
    __table_args__ = (
        Index("ix_ra_canonical_url", "canonical_url", unique=True),
        Index("ix_ra_published_at", "published_at"),
        Index("ix_ra_title_hash", "title_hash"),
        Index("ix_ra_semantic_hash", "semantic_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    canonical_url: Mapped[str] = mapped_column(String(2000), nullable=False, unique=True)
    original_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    semantic_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    normalized_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    keyword_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NaverNewsArticle(Base):
    """네이버 뉴스 검색 API 수집 기사."""

    __tablename__ = "naver_news_articles"
    __table_args__ = (
        Index("ix_nna_keyword_pub", "keyword", "pub_date"),
        Index("ix_nna_fetched_at", "fetched_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    original_link: Mapped[str] = mapped_column(String(1000), nullable=False)
    naver_link: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    pub_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductInfo(Base):
    """상품 마스터 정보. 한국소비자원 API goodId 기준 유니크."""

    __tablename__ = "product_info"
    __table_args__ = (Index("ix_pi_fetched_at", "fetched_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    good_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    good_name: Mapped[str] = mapped_column(String(70), nullable=False)
    good_unit_div_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    good_base_cnt: Mapped[str | None] = mapped_column(String(10), nullable=True)
    good_smlcls_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    detail_mean: Mapped[str | None] = mapped_column(String(200), nullable=True)
    good_total_cnt: Mapped[str | None] = mapped_column(String(15), nullable=True)
    good_total_div_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    product_entp_code: Mapped[str | None] = mapped_column(String(70), nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
