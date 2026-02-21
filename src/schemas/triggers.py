from datetime import datetime

from pydantic import BaseModel, Field

from src.db.enums import TriggerType


class UpdateTriggerRequest(BaseModel):
    """트리거 수정 요청"""

    summary: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="트리거 요약 내용",
        examples=["대법원 최종 판결 확정"],
    )
    type: TriggerType | None = Field(
        default=None,
        description="트리거 유형 (article, ruling, announcement, correction, status_change)",
        examples=["ruling"],
    )
    occurredAt: datetime | None = Field(
        default=None,
        description="트리거 발생 일시 (ISO 8601)",
        examples=["2025-06-15T14:00:00Z"],
    )
