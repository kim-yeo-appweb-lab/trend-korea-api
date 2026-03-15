"""알림 관련 Pydantic V2 스키마."""

from pydantic import BaseModel, Field


class CreateAlertRuleRequest(BaseModel):
    """알림 규칙 생성 요청."""

    keyword: str | None = Field(default=None, description="키워드 필터")
    minImportance: float | None = Field(default=None, description="최소 중요도 (0.0~1.0)")


class AlertRuleResponse(BaseModel):
    """알림 규칙 응답."""

    id: str = Field(description="규칙 ID")
    keyword: str | None = Field(default=None, description="키워드 필터")
    minImportance: float | None = Field(default=None, description="최소 중요도")
    isActive: bool = Field(description="활성 여부")
    createdAt: str = Field(description="생성 일시")


class NotificationResponse(BaseModel):
    """알림 응답."""

    id: str = Field(description="알림 ID")
    type: str = Field(description="알림 유형")
    title: str = Field(description="알림 제목")
    message: str = Field(description="알림 메시지")
    entityType: str | None = Field(default=None, description="관련 엔티티 유형")
    entityId: str | None = Field(default=None, description="관련 엔티티 ID")
    isRead: bool = Field(description="읽음 여부")
    createdAt: str = Field(description="생성 일시")
