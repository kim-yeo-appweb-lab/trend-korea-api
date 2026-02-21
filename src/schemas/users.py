from pydantic import BaseModel, Field


class UpdateMeRequest(BaseModel):
    """내 정보 수정 요청 (변경할 필드만 포함)"""

    nickname: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
        description="변경할 닉네임 (2~20자)",
        examples=["새닉네임"],
    )
    profileImage: str | None = Field(
        default=None,
        max_length=500,
        description="프로필 이미지 URL",
        examples=["https://example.com/images/profile.jpg"],
    )


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""

    currentPassword: str = Field(
        min_length=8,
        max_length=72,
        description="현재 비밀번호",
        examples=["OldP@ss123"],
    )
    newPassword: str = Field(
        min_length=8,
        max_length=72,
        description="새 비밀번호 (8~72자)",
        examples=["NewP@ss456"],
    )


class SocialConnectRequest(BaseModel):
    """SNS 계정 연동 요청"""

    provider: str = Field(
        pattern="^(kakao|naver|google)$",
        description="연동할 SNS 제공자 (kakao, naver, google)",
        examples=["kakao"],
    )
    code: str = Field(
        min_length=1,
        description="OAuth 인가 코드",
        examples=["authorization_code_from_provider"],
    )


class SocialDisconnectRequest(BaseModel):
    """SNS 계정 연동 해제 요청"""

    provider: str = Field(
        pattern="^(kakao|naver|google)$",
        description="해제할 SNS 제공자 (kakao, naver, google)",
        examples=["kakao"],
    )
