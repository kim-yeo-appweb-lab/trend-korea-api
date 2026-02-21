# Python Docstring

## 기본 스타일: 한국어 한 줄 요약

이 프로젝트에서는 간결한 한 줄 docstring을 사용한다.

```python
class AuthService:
    """인증 관련 비즈니스 로직"""

class CursorPagination(BaseModel):
    """커서 기반 페이지네이션 파라미터"""
```

## 작성 기준

### 작성이 필요한 경우

```python
# Pydantic 모델 — Swagger에 표시되므로 작성
class RegisterRequest(BaseModel):
    """회원가입 요청"""

# 동작이 자명하지 않은 유틸리티 함수
def normalize_keyword(raw: str) -> str:
    """형태소 분석 후 명사만 추출하여 정규화된 키워드를 반환한다."""

# 복잡한 로직을 가진 서비스 메서드
def rotate_refresh_token(self, old_token: str) -> AuthTokens:
    """리프레시 토큰을 갱신하고 이전 토큰을 블랙리스트에 등록한다."""
```

### 작성하지 않는 경우

```python
# 메서드명으로 자명한 경우
def get_user_by_email(self, email: str) -> User | None:
    ...

# 단순 CRUD
def create(self, *, data: CreateDTO) -> Model:
    ...

def delete(self, *, id: str) -> None:
    ...

# __init__은 항상 생략
def __init__(self, repository: AuthRepository) -> None:
    self.repository = repository
```

## 복수행이 필요한 경우 (예외적)

메서드명만으로 부족할 때 Google 스타일로 확장한다.

```python
def schedule_crawl(
    self,
    *,
    sources: list[str],
    cron: str,
    retry_count: int = 3,
) -> Job:
    """지정된 소스에 대한 크롤링 스케줄을 등록한다.

    Args:
        sources: 크롤링 대상 URL 목록.
        cron: cron 표현식 (예: "0 9 * * *").
        retry_count: 실패 시 재시도 횟수.

    Raises:
        SchedulerError: cron 표현식이 유효하지 않을 때.
    """
```
