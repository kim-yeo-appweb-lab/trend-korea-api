from pydantic import BaseModel, Field


class PostListQuery(BaseModel):
    """게시글 목록 조회 파라미터"""

    size: int = Field(
        default=20,
        ge=1,
        le=100,
        alias="page[size]",
        description="한 페이지에 조회할 게시글 수",
        examples=[20],
    )
    cursor: str | None = Field(
        default=None,
        alias="page[cursor]",
        description="다음 페이지 커서 토큰",
        examples=["eyJvZmZzZXQiOiAyMH0="],
    )
    tab: str = Field(
        default="latest",
        description="탭 필터 (latest: 최신, popular: 인기)",
        examples=["latest"],
    )
    sort: str = Field(
        default="-createdAt",
        description="정렬 기준 (접두사 `-`는 내림차순)",
        examples=["-createdAt"],
    )


class CreatePostRequest(BaseModel):
    """게시글 작성 요청"""

    title: str = Field(
        min_length=1,
        max_length=100,
        description="게시글 제목 (1~100자)",
        examples=["오늘의 이슈 정리"],
    )
    content: str = Field(
        min_length=1,
        description="게시글 본문 (Markdown 지원)",
        examples=["오늘 주요 이슈를 정리해 보았습니다.\n\n## 1. 정치\n내용..."],
    )
    tagIds: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="연관 태그 ID 목록 (최대 3개)",
        examples=[["tag-uuid-1"]],
    )
    isAnonymous: bool = Field(
        default=False,
        description="익명 게시 여부",
        examples=[False],
    )


class UpdatePostRequest(BaseModel):
    """게시글 수정 요청 (변경할 필드만 포함)"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="변경할 제목",
        examples=["수정된 제목"],
    )
    content: str | None = Field(
        default=None,
        min_length=1,
        description="변경할 본문",
        examples=["수정된 본문 내용입니다."],
    )
    tagIds: list[str] | None = Field(
        default=None,
        max_length=3,
        description="변경할 태그 ID 목록 (최대 3개)",
        examples=[["tag-uuid-1"]],
    )


class CommentListQuery(BaseModel):
    """댓글 목록 조회 파라미터"""

    size: int = Field(
        default=20,
        ge=1,
        le=100,
        alias="page[size]",
        description="한 페이지에 조회할 댓글 수",
        examples=[20],
    )
    cursor: str | None = Field(
        default=None,
        alias="page[cursor]",
        description="다음 페이지 커서 토큰",
        examples=["eyJvZmZzZXQiOiAyMH0="],
    )


class CreateCommentRequest(BaseModel):
    """댓글 작성 요청"""

    content: str = Field(
        min_length=1,
        description="댓글 내용",
        examples=["좋은 분석이네요!"],
    )
    parentId: str | None = Field(
        default=None,
        description="부모 댓글 ID (대댓글인 경우)",
        examples=["comment-uuid-1"],
    )


class VoteRequest(BaseModel):
    """게시글 추천/비추천 요청"""

    type: str = Field(
        pattern="^(like|dislike)$",
        description="추천 유형 (like: 추천, dislike: 비추천)",
        examples=["like"],
    )


class UpdateCommentRequest(BaseModel):
    """댓글 수정 요청"""

    content: str = Field(
        min_length=1,
        description="변경할 댓글 내용",
        examples=["수정된 댓글입니다."],
    )
