from datetime import datetime

from pydantic import BaseModel, Field


class CreateSourceRequest(BaseModel):
    """출처 등록 요청"""

    url: str = Field(
        min_length=1,
        max_length=2000,
        description="기사/자료 URL",
        examples=["https://www.example.com/news/12345"],
    )
    title: str = Field(
        min_length=1,
        max_length=200,
        description="기사/자료 제목",
        examples=["정부, 새 경제 정책 발표"],
    )
    publisher: str = Field(
        min_length=1,
        max_length=100,
        description="발행 매체명",
        examples=["한국일보"],
    )
    publishedAt: datetime = Field(
        description="기사 발행 일시 (ISO 8601)",
        examples=["2025-06-15T09:00:00Z"],
    )
