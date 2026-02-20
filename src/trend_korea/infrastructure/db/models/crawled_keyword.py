from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from trend_korea.infrastructure.db.models.base import Base


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
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
