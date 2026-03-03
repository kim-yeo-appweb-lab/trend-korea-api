from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


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
