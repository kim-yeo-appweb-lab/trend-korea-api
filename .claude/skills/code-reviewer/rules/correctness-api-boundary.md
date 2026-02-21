---
title: API Boundary Validation
impact: HIGH
category: correctness
tags: pydantic, validation, query, api, boundary
---

# API Boundary Validation

API 경계에서 입력값 제약 조건이 적절히 설정되었는지 확인합니다.

## Why This Matters

입력값 상한이 없는 API는 심각한 문제를 야기합니다:
- **서비스 거부(DoS) 공격**: 공격자가 극단적으로 큰 값을 전송하여 서버 과부하 유발
- **메모리 과다 사용**: 무제한 배열이나 문자열로 인한 메모리 폭주
- **느린 쿼리**: 상한 없는 limit으로 전체 테이블 스캔 발생
- **데이터 무결성**: 유효하지 않은 입력값이 데이터베이스에 저장

## ❌ Incorrect

### 1. Pydantic Field 제약 미설정

문자열 길이 제한이 없어 무제한 데이터가 입력될 수 있습니다:

```python
# ❌ 문자열 길이 제한 없음
class PostCreateRequest(BaseModel):
    title: str  # 길이 제한 없음 - 수 GB 문자열 가능
    content: str  # 길이 제한 없음
    category: str  # 빈 문자열도 허용
```

### 2. Query 파라미터에 상한 없는 limit

limit에 상한이 없어 전체 데이터를 한 번에 요청할 수 있습니다:

```python
# ❌ limit 상한 없음
@router.get("/posts")
def list_posts(
    limit: int = Query(ge=1),  # limit=1000000 가능!
    offset: int = Query(ge=0, default=0),
    db: DbSession = Depends(get_db_session),
):
    stmt = select(Post).limit(limit).offset(offset)
    posts = db.execute(stmt).scalars().all()
    return success_response(data=posts)
```

### 3. 배열 길이 무제한

배열 크기에 제한이 없어 과도한 요청이 가능합니다:

```python
# ❌ 배열 길이 무제한
class BulkCreateRequest(BaseModel):
    items: list[str]  # 수백만 개의 항목 전송 가능
    tag_ids: list[int]  # 무제한 태그 연결 가능
```

### 4. 페이지네이션 없는 목록 조회

전체 데이터를 한 번에 반환하여 메모리 부족을 유발합니다:

```python
# ❌ 페이지네이션 없이 전체 목록 반환
@router.get("/users")
def list_users(db: DbSession):
    stmt = select(User)
    users = db.execute(stmt).scalars().all()  # 수십만 건 한 번에 조회
    return success_response(data=users)
```

## ✅ Correct

### 1. Pydantic Field 제약 설정

모든 필드에 적절한 제약 조건을 설정합니다:

```python
# ✅ 적절한 길이/범위 제한 설정
class PostCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
        description="게시글 제목",
        examples=["2025 트렌드 키워드 분석"],
    )
    content: str = Field(
        min_length=1,
        max_length=10000,
        description="게시글 내용",
    )
    category: str = Field(
        min_length=1,
        max_length=50,
        description="카테고리",
        examples=["트렌드"],
    )
```

### 2. Query 파라미터에 적절한 상한 설정

limit와 offset에 상한을 지정합니다:

```python
# ✅ limit에 상한, offset에 기본값 설정
@router.get("/posts")
def list_posts(
    limit: int = Query(ge=1, le=100, default=20, description="페이지당 항목 수"),
    offset: int = Query(ge=0, default=0, description="시작 위치"),
    db: DbSession = Depends(get_db_session),
):
    stmt = select(Post).limit(limit).offset(offset)
    posts = db.execute(stmt).scalars().all()
    db.commit()
    return success_response(data=[PostResponse.model_validate(p) for p in posts])
```

### 3. 배열 길이 제한

배열 필드에 최대 길이를 설정합니다:

```python
# ✅ 배열 길이 제한
class BulkCreateRequest(BaseModel):
    items: list[str] = Field(
        max_length=50,
        description="일괄 생성 항목 (최대 50개)",
    )
    tag_ids: list[int] = Field(
        max_length=10,
        description="태그 ID 목록 (최대 10개)",
    )
```

### 4. 페이지네이션 적용

목록 조회에 항상 페이지네이션을 적용합니다:

```python
# ✅ 페이지네이션 필수 적용
@router.get("/users")
def list_users(
    limit: int = Query(ge=1, le=100, default=20),
    offset: int = Query(ge=0, default=0),
    db: DbSession = Depends(get_db_session),
):
    # 총 개수 조회
    count_stmt = select(func.count()).select_from(User)
    total = db.execute(count_stmt).scalar_one()

    # 페이지네이션 적용
    stmt = select(User).limit(limit).offset(offset)
    users = db.execute(stmt).scalars().all()
    db.commit()

    return success_response(
        data=[UserResponse.model_validate(u) for u in users],
        meta={"total": total, "limit": limit, "offset": offset},
    )
```

### 5. 숫자 필드 범위 제한

숫자 값에도 적절한 범위를 설정합니다:

```python
# ✅ 숫자 범위 제한
class EventCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: int = Field(ge=1, le=10, description="우선순위 (1~10)")
    max_participants: int = Field(ge=1, le=10000, description="최대 참여 인원")
```

## Checklist

- [ ] **모든 문자열 필드에 `min_length`/`max_length` 설정**
- [ ] **모든 숫자 필드에 `ge`/`le` 범위 설정**
- [ ] **배열 필드에 `max_length` 설정**
- [ ] **목록 조회 API에 페이지네이션 필수 적용** (`limit`/`offset` 또는 커서 기반)
- [ ] **Query 파라미터의 `limit`에 상한값 설정** (일반적으로 100 이하)
- [ ] **기본값(default) 적절히 설정**: limit 기본값 20, offset 기본값 0
- [ ] **Field에 description과 examples 포함** (Swagger 문서화)
- [ ] **선택적 필드에 `None` 기본값 명시**

## References

- [Pydantic V2 Field Validators](https://docs.pydantic.dev/latest/concepts/fields/)
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)
- [OWASP API Security - Unrestricted Resource Consumption](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/)
