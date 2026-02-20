from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from trend_korea.domain.enums import TagType
from trend_korea.infrastructure.db.models.base import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[TagType] = mapped_column(Enum(TagType), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
