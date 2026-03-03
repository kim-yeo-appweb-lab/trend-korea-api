"""뉴스 업데이트 분류 결과 모델.

테이블 구조:
  event_updates — 기사별 분류 결과 (NEW/MINOR_UPDATE/MAJOR_UPDATE/DUP)
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.enums import UpdateType


class EventUpdate(Base):
    """기사 분류 결과. 이슈 타임라인의 구성 요소."""

    __tablename__ = "event_updates"
    __table_args__ = (
        Index("ix_eu_issue_created", "issue_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    issue_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    article_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("raw_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    update_type: Mapped[UpdateType] = mapped_column(
        Enum(UpdateType), nullable=False
    )
    update_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    major_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    diff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicate_of_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
