"""수집된 뉴스 기사 정규화 저장 모델.

테이블 구조:
  raw_articles — 크롤링/네이버 API로 수집한 기사 (URL 정규화 + 해시 기반 중복 제거)
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


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
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
