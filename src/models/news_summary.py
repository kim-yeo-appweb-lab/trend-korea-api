"""뉴스 키워드 요약 결과 저장 모델.

테이블 구조:
  news_summary_batches     — 요약 실행 단위 (1회 LLM 호출 = 1 배치)
  news_keyword_summaries   — 키워드별 요약 결과
  news_summary_tags        — 요약별 자동생성 태그 (정규화)
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class NewsSummaryBatch(Base):
    """요약 실행 배치. 1회 LLM 호출 단위."""

    __tablename__ = "news_summary_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)  # openai, gemini, ollama
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    total_keywords: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_articles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summarized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    summaries: Mapped[list["NewsKeywordSummary"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class NewsKeywordSummary(Base):
    """키워드별 뉴스 요약."""

    __tablename__ = "news_keyword_summaries"
    __table_args__ = (
        Index("ix_nks_keyword_created", "keyword", "created_at"),
        Index("ix_nks_category", "category"),
        Index("ix_nks_sentiment", "sentiment"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("news_summary_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # ["point1", ...]
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False, default="neutral")
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="society")
    article_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articles: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # [{title, url, ...}]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    batch: Mapped["NewsSummaryBatch"] = relationship(back_populates="summaries")
    tags: Mapped[list["NewsSummaryTag"]] = relationship(
        back_populates="summary", cascade="all, delete-orphan"
    )


class NewsSummaryTag(Base):
    """요약별 자동생성 태그. 정규화된 조인 테이블."""

    __tablename__ = "news_summary_tags"
    __table_args__ = (
        Index("ix_nst_tag", "tag"),
        Index("ix_nst_summary_tag", "summary_id", "tag", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    summary_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("news_keyword_summaries.id", ondelete="CASCADE"),
        nullable=False,
    )
    tag: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    summary: Mapped["NewsKeywordSummary"] = relationship(back_populates="tags")
