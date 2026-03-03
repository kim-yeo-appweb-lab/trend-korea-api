"""네이버 뉴스 검색 결과 저장 모델.

테이블 구조:
  naver_news_articles — 네이버 뉴스 검색 API로 수집한 기사
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


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
