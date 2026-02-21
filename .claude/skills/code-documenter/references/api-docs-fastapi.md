# FastAPI API 문서화

## Endpoint 문서화 패턴

```python
from fastapi import APIRouter, Query, status

from trend_korea.api.schemas.common import RESPONSE_400, RESPONSE_401, ErrorResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post(
    "/register",
    summary="회원가입",
    description="이메일/비밀번호로 새 계정을 생성합니다.",
    status_code=status.HTTP_201_CREATED,
    responses={
        **RESPONSE_400,
        409: {
            "description": "이미 가입된 이메일 (`E_CONFLICT_001`)",
            "model": ErrorResponse,
        },
    },
)
def register(payload: RegisterRequest, db: DbSession):
    ...
```

### 필수 요소

| 요소 | 설명 |
|------|------|
| `summary` | 한국어 짧은 제목 |
| `description` | 한국어 상세 설명 |
| `status_code` | 성공 상태 코드 |
| `responses` | 에러 응답 (공통 상수 + endpoint별 에러) |

### 에러 응답 작성

공통 에러는 `RESPONSE_400`, `RESPONSE_401` 등 상수를 재사용하고, endpoint 고유 에러만 직접 정의한다.

```python
responses={
    **RESPONSE_400,
    **RESPONSE_401,
    404: {
        "description": "게시글을 찾을 수 없음 (`E_RESOURCE_001`)",
        "model": ErrorResponse,
    },
}
```

에러 코드 형식: `E_[도메인]_[번호]` (예: `E_AUTH_001`, `E_VALID_001`, `E_CONFLICT_001`)

## Pydantic Schema 문서화 패턴

```python
from pydantic import BaseModel, Field, EmailStr

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
```

### Field 필수 속성

| 속성 | 설명 |
|------|------|
| `description` | 한국어 설명 (제약조건 포함) |
| `examples` | 실제적인 예시값 (배열) |
| 검증 규칙 | `min_length`, `max_length`, `ge`, `le`, `pattern` 등 |

## Query/Path 파라미터 문서화

```python
@router.get("/search")
def search(
    q: str = Query(min_length=1, description="검색어 (최소 1자)"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="한 페이지에 조회할 결과 수"),
):
    ...
```

## Router 설정

```python
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "리소스를 찾을 수 없음"}},
)
```
