from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """회원가입 요청"""

    nickname: str = Field(
        min_length=2,
        max_length=20,
        description="사용자 닉네임 (2~20자)",
        examples=["트렌드워처"],
    )
    email: EmailStr = Field(
        description="이메일 주소",
        examples=["user@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=72,
        description="비밀번호 (8~72자)",
        examples=["SecureP@ss123"],
    )


class LoginRequest(BaseModel):
    """로그인 요청"""

    email: EmailStr = Field(
        description="가입된 이메일 주소",
        examples=["user@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=72,
        description="비밀번호",
        examples=["SecureP@ss123"],
    )


class RefreshRequest(BaseModel):
    """토큰 갱신 요청"""

    refreshToken: str = Field(
        description="로그인 시 발급받은 리프레시 토큰",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )


class SocialLoginRequest(BaseModel):
    """SNS 로그인 요청"""

    provider: str = Field(
        pattern="^(kakao|naver|google)$",
        description="SNS 제공자 (kakao, naver, google)",
        examples=["kakao"],
    )
    code: str = Field(
        min_length=1,
        description="OAuth 인가 코드",
        examples=["authorization_code_from_provider"],
    )
    redirectUri: str = Field(
        min_length=1,
        description="OAuth 리다이렉트 URI (프론트엔드 콜백 URL)",
        examples=["https://example.com/auth/callback"],
    )


class WithdrawRequest(BaseModel):
    """회원탈퇴 요청"""

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=72,
        description="현재 비밀번호 (이메일 가입 사용자만 필수, SNS 전용 사용자는 생략 가능)",
        examples=["SecureP@ss123"],
    )
