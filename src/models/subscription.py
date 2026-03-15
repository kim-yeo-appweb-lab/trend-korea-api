"""키워드 구독 모델."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class KeywordSubscription(Base):
    """키워드 구독."""

    __tablename__ = "keyword_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "keyword", name="uq_ks_user_keyword"),)


class KeywordMatch(Base):
    """키워드 매칭 기록."""

    __tablename__ = "keyword_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("keyword_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("raw_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_km_subscription_created", "subscription_id", "created_at"),)
