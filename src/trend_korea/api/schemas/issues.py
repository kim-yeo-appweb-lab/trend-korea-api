from datetime import datetime

from pydantic import BaseModel, Field


class IssueListQuery(BaseModel):
    size: int = Field(default=20, ge=1, le=100, alias="page[size]")
    cursor: str | None = Field(default=None, alias="page[cursor]")
    sort: str = "-latestTriggerAt"
    status: str | None = Field(default=None, alias="filter[status]")
    from_at: datetime | None = Field(default=None, alias="filter[from]")
    to_at: datetime | None = Field(default=None, alias="filter[to]")
