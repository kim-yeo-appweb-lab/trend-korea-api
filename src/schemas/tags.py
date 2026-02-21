from pydantic import BaseModel, Field

from src.db.enums import TagType


class CreateTagRequest(BaseModel):
    """태그 생성 요청"""

    name: str = Field(
        min_length=1,
        max_length=50,
        description="태그 이름",
        examples=["정치"],
    )
    type: TagType = Field(
        description="태그 유형 (category: 주제 분류, region: 지역)",
        examples=["category"],
    )
    slug: str = Field(
        min_length=1,
        max_length=50,
        description="URL에 사용할 슬러그 (영문 소문자, 하이픈)",
        examples=["politics"],
    )


class UpdateTagRequest(BaseModel):
    """태그 수정 요청"""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="변경할 태그 이름",
        examples=["경제"],
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="변경할 슬러그",
        examples=["economy"],
    )
