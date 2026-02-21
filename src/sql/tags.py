from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from src.db.enums import TagType
from src.models.tags import Tag


class TagRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tags(self, *, tag_type: str | None, search: str | None) -> list[Tag]:
        stmt = select(Tag)
        if tag_type and tag_type != "all":
            stmt = stmt.where(Tag.type == TagType(tag_type))
        if search:
            stmt = stmt.where(Tag.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(asc(Tag.name))
        return self.db.execute(stmt).scalars().all()

    def create_tag(self, *, name: str, tag_type: str, slug: str) -> Tag:
        now = datetime.now(timezone.utc)
        tag = Tag(
            id=str(uuid4()),
            name=name,
            type=TagType(tag_type),
            slug=slug,
            updated_at=now,
        )
        self.db.add(tag)
        self.db.flush()
        return tag

    def get_tag(self, tag_id: str) -> Tag | None:
        stmt = select(Tag).where(Tag.id == tag_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_tag(self, *, tag: Tag, name: str | None, slug: str | None) -> Tag:
        if name is not None:
            tag.name = name
        if slug is not None:
            tag.slug = slug
        tag.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return tag

    def delete_tag(self, tag: Tag) -> None:
        self.db.delete(tag)
        self.db.flush()
