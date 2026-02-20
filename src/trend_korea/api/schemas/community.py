from pydantic import BaseModel, Field


class PostListQuery(BaseModel):
    size: int = Field(default=20, ge=1, le=100, alias="page[size]")
    cursor: str | None = Field(default=None, alias="page[cursor]")
    tab: str = Field(default="latest")
    sort: str = Field(default="-createdAt")


class CreatePostRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    tagIds: list[str] = Field(default_factory=list, max_length=3)
    isAnonymous: bool = False


class UpdatePostRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)
    tagIds: list[str] | None = Field(default=None, max_length=3)


class CommentListQuery(BaseModel):
    size: int = Field(default=20, ge=1, le=100, alias="page[size]")
    cursor: str | None = Field(default=None, alias="page[cursor]")


class CreateCommentRequest(BaseModel):
    content: str = Field(min_length=1)
    parentId: str | None = None


class VoteRequest(BaseModel):
    type: str = Field(pattern="^(like|dislike)$")


class UpdateCommentRequest(BaseModel):
    content: str = Field(min_length=1)
