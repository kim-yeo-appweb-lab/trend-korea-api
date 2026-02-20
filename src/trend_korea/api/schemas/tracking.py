from pydantic import BaseModel, Field


class TrackingQuery(BaseModel):
    size: int = Field(default=20, ge=1, le=100, alias="page[size]")
    cursor: str | None = Field(default=None, alias="page[cursor]")
    sort: str = Field(default="-latestTriggerAt")
