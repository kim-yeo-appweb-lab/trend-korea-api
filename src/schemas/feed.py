"""Feed 관련 Pydantic V2 스키마."""

from pydantic import BaseModel, Field


class FeedArticleResponse(BaseModel):
    """피드 항목 내 기사 정보."""

    title: str = Field(description="기사 제목")
    source: str | None = Field(default=None, description="기사 출처")
    publishedAt: str | None = Field(default=None, description="기사 발행 일시")
    url: str = Field(description="기사 URL")


class LiveFeedItemResponse(BaseModel):
    """실시간 피드 항목."""

    id: str = Field(description="피드 항목 ID")
    issueId: str | None = Field(default=None, description="연결된 이슈 ID")
    issueTitle: str | None = Field(default=None, description="연결된 이슈 제목")
    updateType: str = Field(description="업데이트 유형 (NEW, MINOR_UPDATE, MAJOR_UPDATE)")
    updateScore: float = Field(description="업데이트 점수")
    feedType: str = Field(description="피드 유형 (breaking, major, all)")
    rankScore: float = Field(description="랭킹 점수")
    article: FeedArticleResponse = Field(description="기사 정보")
    majorReasons: list[str] = Field(default_factory=list, description="MAJOR 판정 근거")
    diffSummary: str | None = Field(default=None, description="변경 요약")
    createdAt: str = Field(description="생성 일시")


class TopStoryItemResponse(BaseModel):
    """Top Stories 항목."""

    rank: int = Field(description="랭킹 순위")
    issueId: str = Field(description="이슈 ID")
    issueTitle: str = Field(description="이슈 제목")
    score: float = Field(description="종합 점수")
    recentUpdates: int = Field(description="최근 24시간 업데이트 수")
    trackedCount: int = Field(description="추적자 수")
    lastUpdateAt: str | None = Field(default=None, description="마지막 업데이트 시각")


class TimelineItemResponse(BaseModel):
    """이슈 타임라인 항목."""

    updateType: str = Field(description="업데이트 유형")
    summary: str | None = Field(default=None, description="기사 제목/요약")
    diffSummary: str | None = Field(default=None, description="변경 요약")
    sources: list[FeedArticleResponse] = Field(default_factory=list, description="관련 기사 목록")
    occurredAt: str = Field(description="발생 일시")
