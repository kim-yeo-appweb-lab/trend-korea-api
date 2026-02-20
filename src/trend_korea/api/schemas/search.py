from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    q: str = Field(min_length=1)
    type: str = Field(default="all")
    sort: str = Field(default="-relevance")
    size: int = Field(default=20, ge=1, le=100, alias="page[size]")
    cursor: str | None = Field(default=None, alias="page[cursor]")


class SuggestQuery(BaseModel):
    q: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=20)


class RankingQuery(BaseModel):
    limit: int = Field(default=10, ge=1, le=20)
