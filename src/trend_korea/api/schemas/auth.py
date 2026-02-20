from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    nickname: str = Field(min_length=2, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class RefreshRequest(BaseModel):
    refreshToken: str


class SocialLoginRequest(BaseModel):
    provider: str = Field(pattern="^(kakao|naver|google)$")
    code: str = Field(min_length=1)
    redirectUri: str = Field(min_length=1)


class WithdrawRequest(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=72)
