# SQLAlchemy (Sync)

## Engine & Session Setup

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from trend_korea.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Model Definition (2.0 Style)

```python
from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="member")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # 관계 설정
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str]
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")
```

## Database Dependency

```python
from typing import Annotated
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from trend_korea.core.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


# 라우터에서 사용하는 타입 별칭
DbSession = Annotated[Session, Depends(get_db_session)]
```

## Repository Pattern

Repository는 생성자에서 Session을 받고, `flush()`만 호출한다. `commit()`은 라우터에서 담당한다.

```python
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from trend_korea.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_list(self, *, skip: int = 0, limit: int = 20) -> list[User]:
        stmt = select(User).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, *, email: str, nickname: str, hashed_password: str) -> User:
        user = User(email=email, nickname=nickname, hashed_password=hashed_password)
        self.db.add(user)
        self.db.flush()  # flush만, commit은 라우터에서
        return user

    def update_profile(
        self, user: User, *, nickname: str | None, profile_image: str | None
    ) -> User:
        if nickname is not None:
            user.nickname = nickname
        user.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()
```

## CRUD Operations

```python
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session, selectinload

# 단일 조회
def get_user(db: Session, user_id: str) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()

# 관계 포함 조회 (eager loading)
def get_user_with_posts(db: Session, user_id: str) -> User | None:
    stmt = (
        select(User)
        .options(selectinload(User.posts))
        .where(User.id == user_id)
    )
    return db.execute(stmt).scalar_one_or_none()

# 목록 조회
def get_users(db: Session, *, skip: int = 0, limit: int = 20) -> list[User]:
    stmt = select(User).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())

# 생성
def create_user(db: Session, *, email: str, nickname: str, hashed_password: str) -> User:
    user = User(email=email, nickname=nickname, hashed_password=hashed_password)
    db.add(user)
    db.flush()
    return user

# 벌크 업데이트
def deactivate_users(db: Session, user_ids: list[str]) -> int:
    stmt = (
        update(User)
        .where(User.id.in_(user_ids))
        .values(is_active=False)
    )
    result = db.execute(stmt)
    db.flush()
    return result.rowcount

# 삭제
def delete_user(db: Session, user_id: str) -> bool:
    stmt = delete(User).where(User.id == user_id)
    result = db.execute(stmt)
    db.flush()
    return result.rowcount > 0

# 집계
def count_users(db: Session) -> int:
    stmt = select(func.count(User.id))
    return db.execute(stmt).scalar_one()
```

## Transaction Management

Repository에서는 `flush()`만 호출하고, 라우터에서 `db.commit()`을 호출한다.

```python
# 라우터에서의 트랜잭션 관리
@router.post("/register", status_code=201)
def register(payload: RegisterRequest, request: Request, db: DbSession):
    repo = UserRepository(db)
    service = AuthService(repo)
    result = service.register(
        nickname=payload.nickname,
        email=payload.email,
        password=payload.password,
    )
    db.commit()  # 라우터에서 커밋
    return success_response(request=request, data=result, message="회원가입 성공", status_code=201)
```

flush vs commit:
- `flush()` - SQL을 DB로 보내지만 트랜잭션은 유지 (Repository에서 사용)
- `commit()` - 트랜잭션을 확정 (라우터에서 사용)
- `rollback()` - 트랜잭션 취소 (에러 핸들러에서 자동 처리)

## Quick Reference

| 작업 | 방법 |
|------|------|
| 단일 조회 | `db.execute(stmt).scalar_one_or_none()` |
| 목록 조회 | `db.execute(stmt).scalars().all()` |
| Eager loading | `.options(selectinload(...))` |
| 생성 | `db.add(obj)` + `db.flush()` |
| 업데이트 | 속성 변경 후 `db.flush()` |
| 벌크 업데이트 | `update(Model).where(...).values(...)` |
| 삭제 | `db.delete(obj)` 또는 `delete(Model).where(...)` |
| 커밋 | `db.commit()` (라우터에서) |
| 롤백 | `db.rollback()` |
| select 구문 | `select(Model).where(...)` (2.0 style) |
