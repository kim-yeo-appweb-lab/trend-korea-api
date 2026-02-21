---
name: code-documenter
description: Python docstring, FastAPI endpoint 문서화, Pydantic 스키마 문서화에 사용. Swagger/OpenAPI 문서 품질 향상 및 커버리지 리포트 생성.
metadata:
  version: "1.0.0"
  domain: quality
  triggers: documentation, docstrings, API docs, Swagger, FastAPI, Pydantic
  role: specialist
  scope: implementation
  output-format: code
---

# Code Documenter

Trend Korea API 프로젝트 전용 문서화 스킬. Python/FastAPI 코드베이스의 문서화를 담당한다.

## 프로젝트 컨텍스트

- **언어**: Python 3.11+
- **프레임워크**: FastAPI + SQLAlchemy + Pydantic
- **문서화 언어**: 한국어
- **구조**: `src/trend_korea/` (api / application / infrastructure / domain / core)

## 프로젝트 문서화 컨벤션

### Docstring 스타일

한국어 한 줄 요약을 기본으로 한다. Google/NumPy 스타일의 장황한 docstring은 사용하지 않는다.

```python
# ✅ 프로젝트 스타일
class RegisterRequest(BaseModel):
    """회원가입 요청"""

# ❌ 사용하지 않는 스타일
class RegisterRequest(BaseModel):
    """회원가입 요청.

    Attributes:
        nickname: 사용자 닉네임.
        email: 이메일 주소.
    """
```

### 문서화 계층별 기준

| 계층 | 문서화 수준 | 방식 |
|------|------------|------|
| FastAPI Endpoint | 상세 | `summary`, `description`, `responses` |
| Pydantic Schema | 상세 | `Field(description=, examples=)` |
| Service/Repository | 최소 | 메서드명과 타입 힌트로 충분하면 생략 |
| ORM Model | 최소 | 필드명과 제약조건으로 충분하면 생략 |
| Utility 함수 | 필요 시 | 동작이 자명하지 않을 때만 추가 |

### 불필요한 주석 금지

자명한 코드에는 주석을 달지 않는다.

```python
# ❌ 금지
count = 0  # 카운트를 0으로 초기화

# ❌ 금지 — 메서드명으로 이미 자명
def get_user_by_email(self, email: str) -> User | None:
    """이메일로 사용자를 조회한다."""

# ✅ 허용 — 동작이 자명하지 않을 때
def generate_token(self, user_id: str) -> str:
    """UUID v4 기반 일회용 토큰을 생성하고 Redis에 5분 TTL로 저장한다."""
```

## 워크플로우

1. **탐색** — 대상 파일/디렉토리의 현재 문서화 상태 파악
2. **분석** — 미문서화된 코드 식별 (계층별 기준 적용)
3. **문서화** — 프로젝트 컨벤션에 맞게 작성
4. **리포트** — 커버리지 요약 생성

## Reference

| 주제 | 파일 | 참조 시점 |
|------|------|----------|
| FastAPI 문서화 | `references/api-docs-fastapi.md` | Endpoint, Router, Pydantic 문서화 |
| Python Docstring | `references/python-docstrings.md` | 서비스/유틸리티 docstring 작성 |
| 커버리지 리포트 | `references/coverage-reports.md` | 문서화 완료 후 리포트 생성 |

## 제약사항

### 반드시 지킬 것

- 프로젝트의 기존 문서화 컨벤션 준수
- 모든 문서화는 한국어로 작성
- FastAPI endpoint는 `summary` + `description` + `responses` 포함
- Pydantic Field는 `description` + `examples` 포함
- 에러 응답에는 에러 코드(`E_[도메인]_[번호]`) 명시

### 하지 말 것

- 자명한 코드에 불필요한 docstring 추가
- Google/NumPy 스타일의 장황한 docstring 작성
- 영어로 문서화
- 타입 힌트로 이미 명확한 매개변수 설명 반복
