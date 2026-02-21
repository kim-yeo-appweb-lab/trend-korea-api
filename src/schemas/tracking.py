from pydantic import BaseModel, Field


class TrackingQuery(BaseModel):
    """트래킹 목록 조회 파라미터"""

    size: int = Field(
        default=20,
        ge=1,
        le=100,
        alias="page[size]",
        description="한 페이지에 조회할 항목 수",
        examples=[20],
    )
    cursor: str | None = Field(
        default=None,
        alias="page[cursor]",
        description="다음 페이지 커서 토큰",
        examples=["eyJvZmZzZXQiOiAyMH0="],
    )
    sort: str = Field(
        default="-latestTriggerAt",
        description="정렬 기준 (접두사 `-`는 내림차순)",
        examples=["-latestTriggerAt"],
    )
