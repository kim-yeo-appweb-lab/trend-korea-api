from datetime import datetime

from pydantic import BaseModel, Field


class EventListQuery(BaseModel):
    size: int = Field(default=20, ge=1, le=100, alias="page[size]")
    cursor: str | None = Field(default=None, alias="page[cursor]")
    sort: str = "-occurredAt"
    importance: str | None = Field(default=None, alias="filter[importance]")
    verification_status: str | None = Field(default=None, alias="filter[verificationStatus]")
    from_at: datetime | None = Field(default=None, alias="filter[from]")
    to_at: datetime | None = Field(default=None, alias="filter[to]")
