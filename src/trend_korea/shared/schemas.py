from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CursorPagination(BaseModel):
    """커서 기반 페이지네이션 파라미터"""

    size: int = Field(
        ge=1,
        le=100,
        default=20,
        description="한 페이지에 조회할 항목 수",
        examples=[20],
    )
    cursor: str | None = Field(
        default=None,
        description="다음 페이지 조회를 위한 커서 토큰 (첫 페이지는 생략)",
        examples=["eyJvZmZzZXQiOiAyMH0="],
    )


class DateRangeFilter(BaseModel):
    """날짜 범위 필터"""

    from_at: datetime | None = Field(
        default=None,
        alias="filter[from]",
        description="조회 시작 날짜 (ISO 8601)",
        examples=["2025-01-01T00:00:00Z"],
    )
    to_at: datetime | None = Field(
        default=None,
        alias="filter[to]",
        description="조회 종료 날짜 (ISO 8601)",
        examples=["2025-12-31T23:59:59Z"],
    )


# ── 공통 에러 응답 스키마 ──


class ErrorDetailSchema(BaseModel):
    """에러 상세 정보"""

    code: str = Field(
        description="에러 코드 (예: E_AUTH_001, E_VALID_001)",
        examples=["E_AUTH_001"],
    )
    message: str = Field(
        description="에러 메시지 (한국어)",
        examples=["인증 토큰이 없습니다"],
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="에러 상세 (필드 정보, 추가 컨텍스트 등)",
        examples=[{}],
    )


class ErrorResponse(BaseModel):
    """공통 에러 응답 래퍼"""

    success: bool = Field(default=False, description="항상 false")
    error: ErrorDetailSchema
    timestamp: str = Field(
        description="응답 시각 (ISO 8601 UTC)",
        examples=["2025-01-01T00:00:00.000Z"],
    )


# ── 공통 responses 상수 ──

RESPONSE_400: dict = {
    400: {
        "description": "요청 유효성 검증 실패 — 필수 필드 누락(`E_VALID_001`) 또는 형식 오류(`E_VALID_002`)",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "missing_fields": {
                        "summary": "필수 필드 누락",
                        "value": {
                            "success": False,
                            "error": {
                                "code": "E_VALID_001",
                                "message": "필수 필드가 누락되었습니다.",
                                "details": {"fields": ["title", "content"]},
                            },
                            "timestamp": "2025-01-01T00:00:00.000Z",
                        },
                    },
                    "invalid_format": {
                        "summary": "필드 형식 오류",
                        "value": {
                            "success": False,
                            "error": {
                                "code": "E_VALID_002",
                                "message": "필드 형식이 유효하지 않습니다.",
                                "details": {
                                    "errors": [
                                        {"field": "email", "reason": "value is not a valid email address"}
                                    ]
                                },
                            },
                            "timestamp": "2025-01-01T00:00:00.000Z",
                        },
                    },
                }
            }
        },
    }
}

RESPONSE_401: dict = {
    401: {
        "description": "인증 실패 — 토큰 없음(`E_AUTH_001`) 또는 유효하지 않은 토큰(`E_AUTH_003`)",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "E_AUTH_001",
                        "message": "인증 토큰이 없습니다",
                        "details": {},
                    },
                    "timestamp": "2025-01-01T00:00:00.000Z",
                }
            }
        },
    }
}

RESPONSE_403_ADMIN: dict = {
    403: {
        "description": "관리자 권한 필요 (`E_PERM_002`)",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "E_PERM_002",
                        "message": "관리자 권한이 필요합니다",
                        "details": {},
                    },
                    "timestamp": "2025-01-01T00:00:00.000Z",
                }
            }
        },
    }
}

RESPONSE_403_OWNER: dict = {
    403: {
        "description": "작성자 본인 또는 관리자만 가능 (`E_PERM_001`)",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": {
                        "code": "E_PERM_001",
                        "message": "해당 기능에 대한 권한이 없습니다",
                        "details": {},
                    },
                    "timestamp": "2025-01-01T00:00:00.000Z",
                }
            }
        },
    }
}
