from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from trend_korea.domain.enums import SourceEntityType
from trend_korea.infrastructure.db.models.source import Source


class SourceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sources(
        self,
        *,
        page: int,
        limit: int,
        publisher: str | None,
    ) -> tuple[list[Source], int]:
        stmt = select(Source)
        if publisher:
            stmt = stmt.where(Source.publisher == publisher)

        stmt = stmt.order_by(asc(Source.published_at))
        rows = self.db.execute(stmt).scalars().all()
        total = len(rows)
        start = (page - 1) * limit
        end = start + limit
        return rows[start:end], total

    def create_source(
        self,
        *,
        url: str,
        title: str,
        publisher: str,
        published_at: datetime,
    ) -> Source:
        source = Source(
            id=str(uuid4()),
            entity_type=SourceEntityType.EVENT,
            entity_id="manual",
            url=url,
            title=title,
            publisher=publisher,
            published_at=published_at,
        )
        self.db.add(source)
        self.db.flush()
        return source

    def get_source(self, source_id: str) -> Source | None:
        stmt = select(Source).where(Source.id == source_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def delete_source(self, source: Source) -> None:
        self.db.delete(source)
        self.db.flush()
