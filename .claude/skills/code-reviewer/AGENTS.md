# Code Review Guidelines

**A comprehensive guide for AI agents performing code reviews**, organized by priority and impact.

---

## Table of Contents

### Security — **CRITICAL**
1. [SQL Injection Prevention](#sql-injection-prevention)
2. [XSS Prevention](#xss-prevention)
3. [Authentication & Authorization Review](#authentication--authorization-review)

### Performance — **HIGH**
4. [Avoid N+1 Query Problem](#avoid-n-1-query-problem)

### Correctness — **HIGH**
5. [Proper Error Handling](#proper-error-handling)
6. [API Boundary Validation](#api-boundary-validation)

### Maintainability — **MEDIUM**
7. [Use Meaningful Variable Names](#use-meaningful-variable-names)
8. [Add Type Hints](#add-type-hints)

---

## Security

### SQL Injection Prevention

**Impact: CRITICAL** | **Category: security** | **Tags:** sql, security, injection, database, sqlalchemy

SQL 쿼리를 문자열 연결이나 f-string으로 구성하지 마세요. 항상 파라미터화된 쿼리를 사용하여 SQL 인젝션 공격을 방지해야 합니다.

#### ❌ Incorrect

```python
# f-string으로 SQL 구성 - 인젝션 취약
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result

# 공격: get_user("1 OR 1=1") -> 모든 사용자 반환!
```

#### ✅ Correct

```python
from sqlalchemy import select

# ✅ select() 2.0 스타일 - 파라미터 자동 바인딩
def get_user(user_id: int, db: Session) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()

# ✅ text()가 필요한 경우 바운드 파라미터 사용
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE id = :id")
result = db.execute(stmt, {"id": user_id})
```

[Full details: security-sql-injection.md](rules/security-sql-injection.md)

---

### XSS Prevention

**Impact: CRITICAL** | **Category: security** | **Tags:** xss, security, html, fastapi, csp

사용자 입력을 HTML에 삽입할 때 반드시 이스케이프 또는 새니타이징을 수행해야 합니다.

#### ❌ Incorrect

```python
from fastapi.responses import HTMLResponse

# ❌ 사용자 입력을 HTML에 직접 삽입
@router.get("/profile/{username}", response_class=HTMLResponse)
def get_profile_page(username: str):
    return f"<html><body><h1>Welcome, {username}</h1></body></html>"
```

#### ✅ Correct

```python
from markupsafe import escape
from fastapi.responses import HTMLResponse

# ✅ markupsafe로 이스케이프 처리
@router.get("/profile/{username}", response_class=HTMLResponse)
def get_profile_page(username: str):
    safe_username = escape(username)
    return f"<html><body><h1>Welcome, {safe_username}</h1></body></html>"

# ✅ JSONResponse는 기본적으로 안전 (자동 JSON 직렬화)
@router.get("/users/{user_id}")
def get_user(user_id: int, db: DbSession):
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    return success_response(data=UserResponse.model_validate(user))
```

[Full details: security-xss-prevention.md](rules/security-xss-prevention.md)

---

### Authentication & Authorization Review

**Impact: CRITICAL** | **Category: security** | **Tags:** jwt, auth, rbac, authorization, authentication

JWT 검증 및 역할 기반 접근 제어(RBAC)가 올바르게 구현되었는지 확인합니다. 인증/인가 결함은 데이터 유출, 권한 상승 공격으로 이어질 수 있습니다.

#### ❌ Incorrect

```python
# ❌ 인증 의존성 누락 - 누구든 접근 가능
@router.get("/users/me")
def get_my_profile(db: DbSession):
    return success_response(data={"message": "프로필"})

# ❌ 관리자 전용 기능에 일반 회원 권한 사용
@router.delete("/admin/users/{user_id}")
def delete_user(user_id: int, current_user_id: CurrentMemberUserId, db: DbSession):
    db.execute(delete(User).where(User.id == user_id))
    db.commit()
    return success_response(message="삭제 완료")

# ❌ 토큰 타입 미검증 - refresh 토큰을 access로 사용 가능
def get_current_user_id(token: str) -> int:
    payload = decode_token(token)
    return payload.get("sub")  # typ 검증 없음!
```

#### ✅ Correct

```python
# ✅ 적절한 인증 의존성 사용
@router.get("/users/me")
def get_my_profile(current_user_id: CurrentUserId, db: DbSession):
    stmt = select(User).where(User.id == current_user_id)
    user = db.execute(stmt).scalar_one_or_none()
    db.commit()
    return success_response(data=UserResponse.model_validate(user))

# ✅ 관리자 기능에 CurrentAdminUserId 사용
@router.delete("/admin/users/{user_id}")
def delete_user(user_id: int, current_user_id: CurrentAdminUserId, db: DbSession):
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise AppError(code="E_AUTH_002", message="사용자를 찾을 수 없습니다", status_code=401)
    db.delete(user)
    db.commit()
    return success_response(message="삭제 완료")

# ✅ 토큰 타입 검증
def get_current_user_id(token: str) -> int:
    payload: TokenPayload = decode_token(token)
    if payload.get("typ") != "access":
        raise AppError(code="E_AUTH_003", message="유효하지 않은 토큰 타입입니다", status_code=401)
    return int(payload.get("sub"))
```

[Full details: security-auth-review.md](rules/security-auth-review.md)

---

## Performance

### Avoid N+1 Query Problem

**Impact: HIGH** | **Category: performance** | **Tags:** database, performance, orm, queries, sqlalchemy

N+1 쿼리 문제는 목록을 가져오기 위해 1개의 쿼리를 실행한 후, 각 항목의 관련 데이터를 가져오기 위해 N개의 추가 쿼리를 실행할 때 발생합니다.

#### ❌ Incorrect

```python
from sqlalchemy import select

# ❌ N+1 쿼리: lazy loading으로 인한 반복 조회
def get_posts_with_authors(db: Session) -> list[dict]:
    stmt = select(Post)
    posts = db.execute(stmt).scalars().all()  # 1번 쿼리

    for post in posts:
        # N번 쿼리: 각 post마다 author를 개별 조회
        print(f"{post.title} by {post.author.name}")
```

#### ✅ Correct

```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

# ✅ joinedload: 1:1, N:1 관계에 적합 (JOIN 사용)
stmt = select(Post).options(joinedload(Post.author))
posts = db.execute(stmt).scalars().unique().all()

# ✅ selectinload: 1:N, M:N 관계에 적합 (IN 쿼리 사용)
stmt = select(Post).options(selectinload(Post.tags))
posts = db.execute(stmt).scalars().all()

# ✅ Bulk 쿼리 패턴: ID 수집 후 일괄 조회
author_ids = {post.author_id for post in posts}
stmt = select(User).where(User.id.in_(author_ids))
authors = db.execute(stmt).scalars().all()
```

[Full details: performance-n-plus-one.md](rules/performance-n-plus-one.md)

---

## Correctness

### Proper Error Handling

**Impact: HIGH** | **Category: correctness** | **Tags:** errors, exceptions, reliability

항상 에러를 명시적으로 처리하세요. bare except 절을 사용하거나 에러를 묵시적으로 무시하지 마세요.

#### ❌ Incorrect

```python
try:
    result = risky_operation()
except:
    pass  # Silent failure!
```

#### ✅ Correct

```python
try:
    config = json.loads(config_file.read())
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config file: {e}")
    config = get_default_config()
except FileNotFoundError:
    logger.warning("Config file not found, using defaults")
    config = get_default_config()
```

[Full details: correctness-error-handling.md](rules/correctness-error-handling.md)

---

### API Boundary Validation

**Impact: HIGH** | **Category: correctness** | **Tags:** pydantic, validation, query, api, boundary

API 경계에서 입력값 제약 조건이 적절히 설정되었는지 확인합니다. 입력값 상한 없는 API는 서비스 거부 공격, 메모리 과다 사용, 느린 쿼리를 유발합니다.

#### ❌ Incorrect

```python
# ❌ 문자열 길이 제한 없음
class PostCreateRequest(BaseModel):
    title: str
    content: str

# ❌ limit 상한 없음
@router.get("/posts")
def list_posts(limit: int = Query(ge=1), db: DbSession = Depends(get_db_session)):
    stmt = select(Post).limit(limit)  # limit=1000000 가능!
    return db.execute(stmt).scalars().all()

# ❌ 배열 길이 무제한
class BulkCreateRequest(BaseModel):
    items: list[str]  # 수백만 개 가능
```

#### ✅ Correct

```python
# ✅ 적절한 길이/범위 제한 설정
class PostCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)

# ✅ limit에 상한 설정
@router.get("/posts")
def list_posts(
    limit: int = Query(ge=1, le=100, default=20),
    offset: int = Query(ge=0, default=0),
    db: DbSession = Depends(get_db_session),
):
    stmt = select(Post).limit(limit).offset(offset)
    posts = db.execute(stmt).scalars().all()
    db.commit()
    return success_response(data=[PostResponse.model_validate(p) for p in posts])

# ✅ 배열 길이 제한
class BulkCreateRequest(BaseModel):
    items: list[str] = Field(max_length=50)
```

[Full details: correctness-api-boundary.md](rules/correctness-api-boundary.md)

---

## Maintainability

### Use Meaningful Variable Names

**Impact: MEDIUM** | **Category: maintainability** | **Tags:** naming, readability, code-quality

의도를 드러내는 서술적인 이름을 선택하세요. 단일 문자(루프 카운터 제외), 약어, 일반적인 이름을 피하세요.

#### ❌ Incorrect

```python
def calc(x, y, z):
    tmp = x * y
    res = tmp + z
    return res
```

#### ✅ Correct

```python
def calculate_total_price(item_price: float, quantity: int, tax_rate: float) -> float:
    subtotal = item_price * quantity
    total_with_tax = subtotal + (subtotal * tax_rate)
    return total_with_tax
```

[Full details: maintainability-naming.md](rules/maintainability-naming.md)

---

### Add Type Hints

**Impact: MEDIUM** | **Category: maintainability** | **Tags:** types, python, typescript, type-safety

타입 어노테이션을 사용하여 코드를 자기 문서화하고 에러를 조기에 잡으세요.

#### ❌ Incorrect

```python
def get_user(id):
    return users.get(id)
```

#### ✅ Correct

```python
def get_user(id: int) -> Optional[Dict[str, Any]]:
    """Fetch user by ID."""
    return users.get(id)
```

[Full details: maintainability-type-hints.md](rules/maintainability-type-hints.md)

---

## Quick Reference

### Review Checklist

**Security (CRITICAL - review first)**
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Authentication/authorization checks present on all protected endpoints
- [ ] Correct auth dependency level (CurrentAdminUserId for admin features)
- [ ] JWT token type verified
- [ ] Secrets not hardcoded

**Performance (HIGH)**
- [ ] No N+1 queries (use joinedload/selectinload)
- [ ] Appropriate caching
- [ ] No unnecessary database calls
- [ ] Efficient algorithms

**Correctness (HIGH)**
- [ ] Proper error handling
- [ ] Edge cases handled
- [ ] Input validation with Pydantic Field constraints
- [ ] Query parameters bounded (limit with le, offset with ge)
- [ ] List endpoints have pagination
- [ ] No race conditions

**Maintainability (MEDIUM)**
- [ ] Clear variable/function names
- [ ] Type hints present
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] Functions are single-purpose

**Testing**
- [ ] Tests cover new code
- [ ] Edge cases tested
- [ ] Error paths tested

---

## Severity Levels

| Level | Description | Examples | Action |
|-------|-------------|----------|--------|
| **CRITICAL** | Security vulnerabilities, data loss risks | SQL injection, XSS, auth bypass | Block merge, fix immediately |
| **HIGH** | Performance issues, correctness bugs | N+1 queries, missing validation, race conditions | Fix before merge |
| **MEDIUM** | Maintainability, code quality | Naming, type hints, comments | Fix or accept with TODO |
| **LOW** | Style preferences, minor improvements | Formatting, minor refactoring | Optional |

---

## Review Output Format

When performing reviews, structure as:

```markdown
## Security Issues (X found)

### CRITICAL: SQL Injection in `get_user()`
**File:** `api/users.py:45`
**Issue:** User input interpolated directly into SQL query
**Fix:** Use parameterized query with select() 2.0 style

## Performance Issues (X found)

### HIGH: N+1 Query in `list_posts()`
**File:** `routers/posts.py:23`
**Issue:** Lazy loading author in loop
**Fix:** Add `.options(joinedload(Post.author))`

## Summary
- CRITICAL: 1
- HIGH: 1
- MEDIUM: 3
- LOW: 2

**Recommendation:** Address CRITICAL and HIGH issues before merging.
```

---

## References

- Individual rule files in `rules/` directory
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Clean Code by Robert Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
