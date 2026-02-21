---
title: SQL Injection Prevention
impact: CRITICAL
category: security
tags: sql, security, injection, database, sqlalchemy
---

# SQL Injection Prevention

SQL 쿼리를 문자열 연결이나 f-string으로 구성하지 마세요. 항상 파라미터화된 쿼리를 사용하여 SQL 인젝션 공격을 방지해야 합니다.

## Why This Matters

SQL 인젝션은 가장 흔하고 위험한 웹 취약점 중 하나입니다. 공격자는 다음을 수행할 수 있습니다:
- 인가되지 않은 데이터에 접근
- 데이터베이스 레코드 수정 또는 삭제
- 데이터베이스에서 관리자 작업 실행
- 경우에 따라 OS 명령 실행

## ❌ Incorrect

### f-string으로 SQL 구성

사용자 입력이 SQL 쿼리에 직접 삽입되는 경우:

```python
# ❌ 사용자 입력이 쿼리에 직접 포함
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result

# 공격 시나리오: get_user("1 OR 1=1")
# 실행되는 SQL: SELECT * FROM users WHERE id = 1 OR 1=1
# 결과: 모든 사용자 정보 유출!
```

### SQLAlchemy에서의 잘못된 사용

```python
from sqlalchemy import text

# ❌ text() 안에서 f-string 사용
def search_users(keyword: str, db: Session):
    stmt = text(f"SELECT * FROM users WHERE name LIKE '%{keyword}%'")
    return db.execute(stmt).all()

# 공격 시나리오: search_users("'; DROP TABLE users; --")
# 테이블이 삭제될 수 있음!
```

```python
# ❌ where 절에 문자열 직접 삽입
def get_users_by_role(role: str, db: Session):
    stmt = text(f"SELECT * FROM users WHERE role = '{role}'")
    return db.execute(stmt).all()
```

## ✅ Correct

### SQLAlchemy 2.0 ORM (권장)

ORM의 `select()` 구문을 사용하면 파라미터가 자동으로 바인딩됩니다:

```python
from sqlalchemy import select

# ✅ select() 2.0 스타일 - 파라미터 자동 바인딩
def get_user(user_id: int, db: Session) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()

# 안전: user_id는 데이터로 처리되며, 코드로 실행되지 않음
```

### Repository 패턴에서의 안전한 사용

```python
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)  # ✅ 파라미터 자동 바인딩
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)  # ✅ 안전
        return self.db.execute(stmt).scalar_one_or_none()

    def search_by_name(self, keyword: str) -> list[User]:
        stmt = select(User).where(User.name.ilike(f"%{keyword}%"))  # ✅ ORM이 이스케이프 처리
        return self.db.execute(stmt).scalars().all()

    def get_by_ids(self, user_ids: list[int]) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))  # ✅ IN 절도 안전
        return self.db.execute(stmt).scalars().all()
```

### 필터 조건 동적 구성

```python
# ✅ 동적 필터도 ORM을 통해 안전하게 구성
def search_posts(
    db: Session,
    keyword: str | None = None,
    author_id: int | None = None,
    category: str | None = None,
) -> list[Post]:
    stmt = select(Post)

    if keyword:
        stmt = stmt.where(Post.title.ilike(f"%{keyword}%"))
    if author_id:
        stmt = stmt.where(Post.author_id == author_id)
    if category:
        stmt = stmt.where(Post.category == category)

    return db.execute(stmt).scalars().all()
```

### text()로 Raw SQL이 필요한 경우

ORM으로 표현하기 어려운 복잡한 쿼리에는 `text()`와 바운드 파라미터를 사용합니다:

```python
from sqlalchemy import text

# ✅ text()에 바운드 파라미터 사용
def get_user_stats(user_id: int, db: Session):
    stmt = text("""
        SELECT u.id, u.name, COUNT(p.id) as post_count
        FROM users u
        LEFT JOIN posts p ON u.id = p.author_id
        WHERE u.id = :user_id
        GROUP BY u.id, u.name
    """)
    return db.execute(stmt, {"user_id": user_id}).first()

# ✅ 여러 파라미터도 동일하게 바인딩
def search_users_raw(keyword: str, role: str, db: Session):
    stmt = text("""
        SELECT * FROM users
        WHERE name ILIKE :pattern AND role = :role
    """)
    return db.execute(stmt, {"pattern": f"%{keyword}%", "role": role}).all()
```

## Additional Best Practices

### 1. 입력 타입 검증 (Pydantic + FastAPI)

```python
# ✅ Pydantic으로 타입 자동 검증
class UserQuery(BaseModel):
    user_id: int = Field(ge=1, description="사용자 ID")
    keyword: str = Field(max_length=100, description="검색어")

@router.get("/users/{user_id}")
def get_user(user_id: int, db: DbSession):
    # FastAPI가 user_id를 int로 자동 변환 및 검증
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise AppError(code="E_AUTH_002", message="사용자를 찾을 수 없습니다", status_code=401)
    return success_response(data=UserResponse.model_validate(user))
```

### 2. ORM 우선 사용

- ORM은 파라미터화를 자동으로 처리합니다
- 수동 SQL 오류 위험을 줄여줍니다
- 타입 안전성과 추상화를 제공합니다

### 3. 최소 권한 원칙

- 데이터베이스 사용자에게 최소한의 권한만 부여
- SELECT 전용 계정을 읽기 작업에 사용
- 성공적인 인젝션 공격의 피해를 제한

### 4. 입력 검증 (방어 심층 계층)

- 파라미터화가 주요 방어 수단
- 검증은 추가적인 방어 계층으로 활용
- 허용된 문자/패턴 화이트리스트 적용

## Django ORM 참고

Django에서도 ORM을 통해 안전한 쿼리를 구성할 수 있습니다:

```python
# ✅ Django ORM - 안전
User.objects.get(id=user_id)
User.objects.filter(name__icontains=keyword)

# ✅ raw SQL 사용 시 파라미터 바인딩
User.objects.raw("SELECT * FROM users WHERE id = %s", [user_id])
```

## References

- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [SQLAlchemy Using Textual SQL](https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.text)
