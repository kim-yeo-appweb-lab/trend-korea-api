from pydantic import BaseModel, Field


class UpdateMeRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=2, max_length=20)
    profileImage: str | None = Field(default=None, max_length=500)


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(min_length=8, max_length=72)
    newPassword: str = Field(min_length=8, max_length=72)


class SocialConnectRequest(BaseModel):
    provider: str = Field(pattern="^(kakao|naver|google)$")
    code: str = Field(min_length=1)


class SocialDisconnectRequest(BaseModel):
    provider: str = Field(pattern="^(kakao|naver|google)$")
