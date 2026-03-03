"""실시간 피드 항목 모델.

테이블 구조:
  live_feed_items — 피드 노출용 사전 계산된 항목 (breaking/major/all)
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.enums import FeedType


class LiveFeedItem(Base):
    """실시간 피드 항목. 속보/주요/전체 피드를 위한 사전 계산 행."""

    __tablename__ = "live_feed_items"
    __table_args__ = (
        Index(
            "ix_lfi_feed_rank_created",
            "feed_type",
            "rank_score",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    issue_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    update_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("event_updates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feed_type: Mapped[FeedType] = mapped_column(
        Enum(FeedType), nullable=False
    )
    rank_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
