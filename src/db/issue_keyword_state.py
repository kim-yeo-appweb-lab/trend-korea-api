"""이슈-키워드 연결 상태 모델.

테이블 구조:
  issue_keyword_states — 이슈와 정규화된 키워드 간의 매핑 및 활성 상태 관리
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.enums import KeywordLinkStatus


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
        Enum(KeywordLinkStatus), nullable=False, default=KeywordLinkStatus.ACTIVE
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
