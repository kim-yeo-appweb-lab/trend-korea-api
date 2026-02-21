---
title: Avoid N+1 Query Problem
impact: HIGH
category: performance
tags: database, performance, orm, queries, sqlalchemy
---

# Avoid N+1 Query Problem

N+1 쿼리 문제는 코드가 목록을 가져오기 위해 1개의 쿼리를 실행한 후, 각 항목의 관련 데이터를 가져오기 위해 N개의 추가 쿼리를 실행할 때 발생합니다. 심각한 성능 저하의 주요 원인입니다.

## Why This Matters

N+1 쿼리는 가장 흔한 성능 문제 중 하나입니다:
- **10건** -> 11 쿼리 (1 + 10)
- **100건** -> 101 쿼리 (1 + 100)
- **1000건** -> 1001 쿼리 (1 + 1000)

각 쿼리에는 네트워크 지연(~1-50ms)이 있으므로, 1000 쿼리 = 1~50초의 대기 시간이 발생합니다!

## ❌ Incorrect

**문제:** 루프 내에서 관련 데이터를 개별 조회합니다.

### SQLAlchemy - Lazy Loading N+1

```python
# ❌ N+1 쿼리: lazy loading으로 인한 반복 조회
def get_posts_with_authors(db: Session) -> list[dict]:
    stmt = select(Post)
    posts = db.execute(stmt).scalars().all()  # 1번 쿼리: SELECT * FROM posts

    result = []
    for post in posts:
        # N번 쿼리: 각 post마다 author를 개별 조회 (lazy load 발생)
        result.append({
            "title": post.title,
            "author_name": post.author.name,  # SELECT * FROM users WHERE id = ?
        })

    return result

# 100개의 게시글이 있으면: 101번의 데이터베이스 쿼리 실행!
```

### SQLAlchemy - 수동 루프 조회

```python
# ❌ 루프 안에서 개별 쿼리 실행
def get_posts_with_tags(db: Session) -> list[dict]:
    stmt = select(Post)
    posts = db.execute(stmt).scalars().all()  # 1번 쿼리

    result = []
    for post in posts:
        # N번 쿼리: 각 post의 태그를 개별 조회
        tag_stmt = select(Tag).join(PostTag).where(PostTag.post_id == post.id)
        tags = db.execute(tag_stmt).scalars().all()
        result.append({"title": post.title, "tags": [t.name for t in tags]})

    return result
```

## ✅ Correct

### Solution 1: joinedload (1:1, N:1 관계에 적합)

단일 JOIN 쿼리로 관련 데이터를 한 번에 가져옵니다:

```python
from sqlalchemy.orm import joinedload

# ✅ 1번의 JOIN 쿼리로 author를 함께 조회
def get_posts_with_authors(db: Session) -> list[dict]:
    stmt = select(Post).options(joinedload(Post.author))
    posts = db.execute(stmt).scalars().unique().all()
    # 실행 SQL: SELECT posts.*, users.* FROM posts JOIN users ON posts.author_id = users.id

    return [
        {"title": post.title, "author_name": post.author.name}  # 추가 쿼리 없음!
        for post in posts
    ]
```

### Solution 2: selectinload (1:N, M:N 관계에 적합)

별도의 IN 쿼리로 관련 데이터를 효율적으로 가져옵니다:

```python
from sqlalchemy.orm import selectinload

# ✅ 2번의 쿼리로 tags를 함께 조회
def get_posts_with_tags(db: Session) -> list[dict]:
    stmt = select(Post).options(selectinload(Post.tags))
    posts = db.execute(stmt).scalars().all()
    # 실행 SQL:
    # 1. SELECT * FROM posts
    # 2. SELECT * FROM tags WHERE post_id IN (1, 2, 3, ...)

    return [
        {"title": post.title, "tags": [t.name for t in post.tags]}  # 추가 쿼리 없음!
        for post in posts
    ]
```

### Solution 3: 복합 관계 로딩

여러 관계를 동시에 최적화할 수 있습니다:

```python
from sqlalchemy.orm import joinedload, selectinload

# ✅ author는 joinedload, tags와 comments는 selectinload
def get_posts_detail(db: Session) -> list[dict]:
    stmt = (
        select(Post)
        .options(
            joinedload(Post.author),        # 1:1 관계 -> JOIN
            selectinload(Post.tags),         # M:N 관계 -> IN 쿼리
            selectinload(Post.comments),     # 1:N 관계 -> IN 쿼리
        )
        .order_by(Post.created_at.desc())
        .limit(20)
    )
    posts = db.execute(stmt).scalars().unique().all()
    return [PostDetailResponse.model_validate(p) for p in posts]
```

### Solution 4: Bulk 쿼리 패턴 (ORM 관계 없는 경우)

관계 설정 없이 ID를 수집하여 일괄 조회합니다:

```python
# ✅ ID를 모아서 한 번에 조회
def get_posts_with_authors_bulk(db: Session) -> list[dict]:
    # 1번째 쿼리: 게시글 조회
    post_stmt = select(Post).limit(100)
    posts = db.execute(post_stmt).scalars().all()

    # 고유 author ID 수집
    author_ids = {post.author_id for post in posts}

    # 2번째 쿼리: 모든 author를 한 번에 조회
    author_stmt = select(User).where(User.id.in_(author_ids))
    authors = db.execute(author_stmt).scalars().all()
    author_map = {author.id: author for author in authors}

    # author 매핑
    return [
        {
            "title": post.title,
            "author_name": author_map[post.author_id].name,
        }
        for post in posts
    ]

# 총 2번의 쿼리로 완료 (N+1 대비 훨씬 효율적)
```

## Django ORM 참고

Django에서도 동일한 문제가 발생하며, `select_related`/`prefetch_related`로 해결합니다:

```python
# ❌ N+1
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # N번 추가 쿼리

# ✅ 해결: select_related (JOIN)
posts = Post.objects.select_related('author').all()

# ✅ 해결: prefetch_related (별도 쿼리)
posts = Post.objects.prefetch_related('tags').all()
```

## N+1 쿼리 감지

### SQLAlchemy 엔진 로깅

개발 환경에서 실행되는 모든 SQL을 로깅하여 N+1 패턴을 감지합니다:

```python
import logging

# 개발 환경에서 SQL 쿼리 로깅 활성화
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

### echo 옵션 활용

```python
from sqlalchemy import create_engine

# 개발 환경에서만 echo 활성화
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 모든 SQL 출력 (운영 환경에서는 False)
)
```

### 쿼리 카운트 테스트

```python
# 테스트에서 쿼리 수 검증
from unittest.mock import patch

def test_no_n_plus_one(db: Session):
    # 테스트 데이터 생성
    create_test_posts(db, count=10)

    # 쿼리 카운트 확인
    with count_queries(engine) as query_count:
        get_posts_with_authors(db)

    # N+1이 아닌 고정된 쿼리 수 확인
    assert query_count.count <= 3  # 1~3개의 쿼리가 정상
```

## Performance Comparison

```
테스트: 100개의 게시글 + 작성자 조회

N+1 쿼리 (101번 쿼리):
- 로컬 DB: ~101ms (쿼리당 1ms)
- 원격 DB: ~5.1s (지연 50ms x 101)

Eager Loading (1~2번 쿼리):
- 로컬 DB: ~10ms
- 원격 DB: ~50~100ms

-> 10~100배 성능 향상!
```

## Best Practices

- [ ] **joinedload 사용**: 1:1, N:1 관계에 적합 (`Post.author`)
- [ ] **selectinload 사용**: 1:N, M:N 관계에 적합 (`Post.tags`, `Post.comments`)
- [ ] **Bulk 쿼리 패턴**: ORM 관계 없을 때 ID 수집 후 `in_()` 사용
- [ ] **개발 환경에서 SQL 로깅 활성화**: `echo=True` 또는 `logging.getLogger("sqlalchemy.engine")`
- [ ] **쿼리 카운트 테스트 작성**: N+1 회귀 방지
- [ ] **`.unique()` 호출 주의**: `joinedload` 사용 시 `scalars().unique().all()` 필요
- [ ] **페이지네이션과 함께 사용**: `limit()`/`offset()` 적용하여 데이터 양 제한

## References

- [SQLAlchemy Relationship Loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [SQLAlchemy joinedload](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading)
- [SQLAlchemy selectinload](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#select-in-loading)
