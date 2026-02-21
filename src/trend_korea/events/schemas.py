from datetime import datetime

from pydantic import BaseModel, Field

from trend_korea.db.enums import Importance, VerificationStatus


class EventListQuery(BaseModel):
    """사건 목록 조회 파라미터"""

    size: int = Field(
        default=20, ge=1, le=100, alias="page[size]",
        description="한 페이지에 조회할 사건 수", examples=[20],
    )
    cursor: str | None = Field(
        default=None, alias="page[cursor]",
        description="다음 페이지 커서 토큰", examples=["eyJvZmZzZXQiOiAyMH0="],
    )
    sort: str = Field(
        default="-occurredAt",
        description="정렬 기준 (접두사 `-`는 내림차순)", examples=["-occurredAt"],
    )
    importance: str | None = Field(
        default=None, alias="filter[importance]",
        description="중요도 필터 (low, medium, high)", examples=["high"],
    )
    verification_status: str | None = Field(
        default=None, alias="filter[verificationStatus]",
        description="검증 상태 필터 (verified, unverified)", examples=["verified"],
    )
    from_at: datetime | None = Field(
        default=None, alias="filter[from]",
        description="조회 시작 날짜 (ISO 8601)", examples=["2025-01-01T00:00:00Z"],
    )
    to_at: datetime | None = Field(
        default=None, alias="filter[to]",
        description="조회 종료 날짜 (ISO 8601)", examples=["2025-12-31T23:59:59Z"],
    )


class CreateEventRequest(BaseModel):
    """사건 생성 요청"""

    occurredAt: datetime = Field(
        description="사건 발생 일시 (ISO 8601)",
        examples=["2025-06-15T09:00:00Z"],
    )
    title: str = Field(
        min_length=1,
        max_length=200,
        description="사건 제목",
        examples=["국회 본회의 통과"],
    )
    summary: str = Field(
        min_length=1,
        max_length=2000,
        description="사건 요약 설명",
        examples=["국회 본회의에서 해당 법안이 찬성 다수로 통과되었습니다."],
    )
    importance: Importance = Field(
        description="중요도 (low, medium, high)",
        examples=["high"],
    )
    verificationStatus: VerificationStatus = Field(
        description="검증 상태 (verified, unverified)",
        examples=["verified"],
    )
    tagIds: list[str] = Field(
        max_length=3,
        description="연관 태그 ID 목록 (최대 3개)",
        examples=[["tag-uuid-1", "tag-uuid-2"]],
    )
    sourceIds: list[str] = Field(
        min_length=1,
        description="출처 ID 목록 (최소 1개)",
        examples=[["source-uuid-1"]],
    )


class UpdateEventRequest(BaseModel):
    """사건 수정 요청 (변경할 필드만 포함)"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="변경할 사건 제목",
        examples=["수정된 사건 제목"],
    )
    summary: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
        description="변경할 사건 요약",
        examples=["수정된 사건 요약 내용입니다."],
    )
    importance: Importance | None = Field(
        default=None,
        description="변경할 중요도",
        examples=["medium"],
    )
    verificationStatus: VerificationStatus | None = Field(
        default=None,
        description="변경할 검증 상태",
        examples=["verified"],
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
