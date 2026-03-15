"""키워드 구독 관련 Pydantic V2 스키마."""

from pydantic import BaseModel, Field


class CreateSubscriptionRequest(BaseModel):
    """키워드 구독 요청."""

    keyword: str = Field(min_length=1, max_length=200, description="구독할 키워드")


class SubscriptionResponse(BaseModel):
    """키워드 구독 응답."""

    id: str = Field(description="구독 ID")
    keyword: str = Field(description="구독 키워드")
    isActive: bool = Field(description="활성 여부")
    createdAt: str = Field(description="생성 일시")


class KeywordMatchResponse(BaseModel):
    """키워드 매칭 기사 응답."""

    id: str = Field(description="매칭 ID")
    articleId: str = Field(description="기사 ID")
    articleTitle: str = Field(description="기사 제목")
    articleUrl: str = Field(description="기사 URL")
    source: str | None = Field(default=None, description="기사 출처")
    matchedAt: str = Field(description="매칭 시각")
