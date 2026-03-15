from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, ValueEnum
from src.db.enums import IssueStatus, KeywordLinkStatus

issue_tags = Table(
    "issue_tags",
    Base.metadata,
    Column("issue_id", ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

issue_events = Table(
    "issue_events",
    Base.metadata,
    Column("issue_id", ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
)

user_tracked_issues = Table(
    "user_tracked_issues",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("issue_id", ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("tracked_at", DateTime(timezone=True), nullable=False),
)


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IssueStatus] = mapped_column(ValueEnum(IssueStatus), nullable=False, index=True)
    tracker_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    latest_trigger_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IssueKeywordState(Base):
    """이슈-키워드 연결 상태. 키워드 기반 이슈 자동 매칭에 사용."""

    __tablename__ = "issue_keyword_states"
    __table_args__ = (
        Index(
            "ix_iks_keyword_status_seen",
            "normalized_keyword",
            "status",
            "last_seen_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    issue_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_keyword: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[KeywordLinkStatus] = mapped_column(
        ValueEnum(KeywordLinkStatus), nullable=False, default=KeywordLinkStatus.ACTIVE
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IssueKeywordAlias(Base):
    __tablename__ = "issue_keyword_aliases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    alias_keyword: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    canonical_keyword: Mapped[str] = mapped_column(String(200), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_ika_canonical", "canonical_keyword"),)


class IssueRankSnapshot(Base):
    __tablename__ = "issue_rank_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    issue_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    recent_updates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tracked_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_irs_calculated_rank", "calculated_at", "rank"),)
