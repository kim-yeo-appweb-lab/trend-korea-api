# Endpoints & Routing

## Router Setup

```python
from fastapi import APIRouter, Query, Path, Request
from typing import Annotated

from trend_korea.core.deps import DbSession, CurrentUserId, CurrentMemberUserId, CurrentAdminUserId
from trend_korea.core.response import success_response
from trend_korea.core.exceptions import AppError

router = APIRouter(prefix="/users", tags=["users"])
```

## CRUD Endpoints (Service + Repository 패턴)

```python
from trend_korea.repositories.user_repository import UserRepository
from trend_korea.services.user_service import UserService


@router.post(
    "/",
    summary="회원가입",
    status_code=201,
    responses={400: {"description": "잘못된 요청"}, 409: {"description": "이메일 중복"}},
)
def create_user(payload: UserCreateRequest, request: Request, db: DbSession):
    repo = UserRepository(db)
    service = UserService(repo)
    user = service.create(
        email=payload.email,
        nickname=payload.nickname,
        password=payload.password,
    )
    db.commit()
    return success_response(
        request=request, data={"id": user.id}, message="회원가입 성공", status_code=201
    )


@router.get("/", summary="회원 목록 조회")
def list_users(
    request: Request,
    db: DbSession,
    user_id: CurrentMemberUserId,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = UserRepository(db)
    users = repo.get_list(skip=skip, limit=limit)
    return success_response(request=request, data=users)


@router.get("/{user_id}", summary="회원 상세 조회")
def get_user(
    user_id: Annotated[str, Path()],
    request: Request,
    db: DbSession,
    current_user_id: CurrentUserId,
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise AppError(code="E_USER_001", message="사용자를 찾을 수 없습니다", status_code=404)
    return success_response(request=request, data=user)


@router.patch("/{user_id}", summary="회원 정보 수정")
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    request: Request,
    db: DbSession,
    current_user_id: CurrentMemberUserId,
):
    repo = UserRepository(db)
    service = UserService(repo)
    user = service.update_profile(user_id, nickname=payload.nickname)
    db.commit()
    return success_response(request=request, data=user, message="수정 완료")


@router.delete("/{user_id}", summary="회원 삭제", status_code=200)
def delete_user(
    user_id: str,
    request: Request,
    db: DbSession,
    admin_id: CurrentAdminUserId,
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise AppError(code="E_USER_001", message="사용자를 찾을 수 없습니다", status_code=404)
    repo.delete(user)
    db.commit()
    return success_response(request=request, message="삭제 완료")
```

## Custom Dependencies

```python
from fastapi import Depends


def get_pagination(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
) -> dict[str, int]:
    return {"skip": (page - 1) * size, "limit": size}


Pagination = Annotated[dict[str, int], Depends(get_pagination)]


@router.get("/", summary="목록 조회")
def list_items(request: Request, db: DbSession, pagination: Pagination):
    repo = ItemRepository(db)
    items = repo.get_list(skip=pagination["skip"], limit=pagination["limit"])
    return success_response(request=request, data=items)
```

## Query Parameters

```python
@router.get("/search", summary="검색")
def search_users(
    request: Request,
    db: DbSession,
    current_user_id: CurrentUserId,
    q: str = Query(min_length=1, max_length=100, description="검색어"),
    is_active: bool | None = Query(None, description="활성 여부"),
    sort_by: Annotated[str, Query(pattern="^(nickname|email|created_at)$")] = "created_at",
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
):
    repo = UserRepository(db)
    users = repo.search(q=q, is_active=is_active, sort_by=sort_by, order=order)
    return success_response(request=request, data=users)
```

## Include Router

```python
# main.py
from fastapi import FastAPI

from trend_korea.routers import auth, users, posts

app = FastAPI(title="Trend Korea API")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
```

## Response 패턴

`success_response()`는 통일된 응답 포맷을 반환한다. `AppError`는 에러 응답을 위해 사용한다.

```python
from trend_korea.core.response import success_response
from trend_korea.core.exceptions import AppError


# 성공 응답
@router.get("/{item_id}", summary="단일 조회")
def get_item(item_id: str, request: Request, db: DbSession):
    repo = ItemRepository(db)
    item = repo.get_by_id(item_id)
    if not item:
        raise AppError(code="E_ITEM_001", message="항목을 찾을 수 없습니다", status_code=404)
    return success_response(request=request, data=item)


# 커스텀 응답 메타데이터
@router.post("/", summary="생성", status_code=201, responses={
    201: {"description": "생성 성공"},
    400: {"description": "잘못된 요청"},
    409: {"description": "중복"},
})
def create_item(payload: ItemCreateRequest, request: Request, db: DbSession):
    repo = ItemRepository(db)
    service = ItemService(repo)
    item = service.create(name=payload.name)
    db.commit()
    return success_response(
        request=request, data={"id": item.id}, message="생성 성공", status_code=201
    )
```

## Quick Reference

| 패턴 | 용도 |
|------|------|
| `@router.get("/")` | GET 엔드포인트 |
| `@router.post("/", status_code=201)` | POST + 상태 코드 |
| `Query(ge=0)` | 쿼리 파라미터 검증 |
| `Path(gt=0)` | 경로 파라미터 검증 |
| `DbSession` | DB 세션 의존성 |
| `CurrentUserId` | 인증된 사용자 ID |
| `CurrentMemberUserId` | member/admin 역할 필수 |
| `CurrentAdminUserId` | admin 역할 필수 |
| `success_response()` | 통일된 성공 응답 |
| `AppError(code, message, status_code)` | 에러 응답 |
| `db.commit()` | 라우터에서 트랜잭션 커밋 |
