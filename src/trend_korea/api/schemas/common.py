from datetime import datetime

from pydantic import BaseModel, Field


class CursorPagination(BaseModel):
    size: int = Field(ge=1, le=100, default=20)
    cursor: str | None = None


class DateRangeFilter(BaseModel):
    from_at: datetime | None = Field(default=None, alias="filter[from]")
    to_at: datetime | None = Field(default=None, alias="filter[to]")
