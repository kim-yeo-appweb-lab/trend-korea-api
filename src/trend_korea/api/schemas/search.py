from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """통합 검색 파라미터"""

    q: str = Field(
        min_length=1,
        description="검색어 (최소 1자)",
        examples=["경제 정책"],
    )
    type: str = Field(
        default="all",
        description="검색 범위 (all: 전체, events: 사건, issues: 이슈, community: 게시글)",
        examples=["all"],
    )
    sort: str = Field(
        default="-relevance",
        description="정렬 기준 (접두사 `-`는 내림차순, relevance: 관련도, createdAt: 작성일)",
        examples=["-relevance"],
    )
    size: int = Field(
        default=20,
        ge=1,
        le=100,
        alias="page[size]",
        description="한 페이지에 조회할 결과 수",
        examples=[20],
    )
    cursor: str | None = Field(
        default=None,
        alias="page[cursor]",
        description="다음 페이지 커서 토큰",
        examples=["eyJvZmZzZXQiOiAyMH0="],
    )


class SuggestQuery(BaseModel):
    """자동완성 검색어 추천 파라미터"""

    q: str = Field(
        min_length=1,
        description="입력 중인 검색어",
        examples=["경제"],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="최대 추천 수 (1~20)",
        examples=[10],
    )


class RankingQuery(BaseModel):
    """검색어 랭킹 조회 파라미터"""

    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="상위 랭킹 수 (1~20)",
        examples=[10],
    )
