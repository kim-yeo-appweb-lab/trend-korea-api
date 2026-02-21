from datetime import datetime

from pydantic import BaseModel, Field

from trend_korea.db.enums import IssueStatus, TriggerType


class IssueListQuery(BaseModel):
    """이슈 목록 조회 파라미터"""

    size: int = Field(
        default=20, ge=1, le=100, alias="page[size]",
        description="한 페이지에 조회할 이슈 수", examples=[20],
    )
    cursor: str | None = Field(
        default=None, alias="page[cursor]",
        description="다음 페이지 커서 토큰", examples=["eyJvZmZzZXQiOiAyMH0="],
    )
    sort: str = Field(
        default="-latestTriggerAt",
        description="정렬 기준 (접두사 `-`는 내림차순)", examples=["-latestTriggerAt"],
    )
    status: str | None = Field(
        default=None, alias="filter[status]",
        description="이슈 상태 필터 (ongoing, closed, reignited, unverified)", examples=["ongoing"],
    )
    from_at: datetime | None = Field(
        default=None, alias="filter[from]",
        description="조회 시작 날짜 (ISO 8601)", examples=["2025-01-01T00:00:00Z"],
    )
    to_at: datetime | None = Field(
        default=None, alias="filter[to]",
        description="조회 종료 날짜 (ISO 8601)", examples=["2025-12-31T23:59:59Z"],
    )


class CreateIssueRequest(BaseModel):
    """이슈 생성 요청"""

    title: str = Field(
        min_length=1,
        max_length=200,
        description="이슈 제목",
        examples=["교육 정책 개편 논란"],
    )
    description: str = Field(
        min_length=1,
        max_length=5000,
        description="이슈 상세 설명",
        examples=["정부의 교육 정책 개편안에 대한 찬반 논란이 이어지고 있습니다."],
    )
    status: IssueStatus = Field(
        description="이슈 상태 (ongoing, closed, reignited, unverified)",
        examples=["ongoing"],
    )
    tagIds: list[str] = Field(
        max_length=3,
        description="연관 태그 ID 목록 (최대 3개)",
        examples=[["tag-uuid-1"]],
    )
    sourceIds: list[str] = Field(
        min_length=1,
        description="출처 ID 목록 (최소 1개)",
        examples=[["source-uuid-1"]],
    )
    relatedEventIds: list[str] = Field(
        default_factory=list,
        description="관련 사건 ID 목록",
        examples=[["event-uuid-1"]],
    )


class UpdateIssueRequest(BaseModel):
    """이슈 수정 요청 (변경할 필드만 포함)"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="변경할 이슈 제목",
        examples=["수정된 이슈 제목"],
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
        description="변경할 이슈 설명",
        examples=["수정된 이슈 설명입니다."],
    )
    status: IssueStatus | None = Field(
        default=None,
        description="변경할 이슈 상태",
        examples=["closed"],
    )
    tagIds: list[str] | None = Field(
        default=None,
        max_length=3,
        description="변경할 태그 ID 목록 (최대 3개)",
        examples=[["tag-uuid-1"]],
    )
    sourceIds: list[str] | None = Field(
        default=None,
        min_length=1,
        description="변경할 출처 ID 목록 (최소 1개)",
        examples=[["source-uuid-1"]],
    )
    relatedEventIds: list[str] | None = Field(
        default=None,
        description="변경할 관련 사건 ID 목록",
        examples=[["event-uuid-1"]],
    )


class CreateTriggerRequest(BaseModel):
    """트리거 생성 요청"""

    occurredAt: datetime = Field(
        description="트리거 발생 일시 (ISO 8601)",
        examples=["2025-06-15T14:00:00Z"],
    )
    summary: str = Field(
        min_length=1,
        max_length=500,
        description="트리거 요약 내용",
        examples=["법원, 해당 사건에 대한 판결 선고"],
    )
    type: TriggerType = Field(
        description="트리거 유형 (article, ruling, announcement, correction, status_change)",
        examples=["ruling"],
    )
    sourceIds: list[str] = Field(
        min_length=1,
        description="출처 ID 목록 (최소 1개)",
        examples=[["source-uuid-1"]],
    )
