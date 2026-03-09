## 코드 스타일

- ruff: line-length=100, target-version=py311
- 타입 힌트 필수 (`X | None` 스타일, `Optional[X]` 사용 금지)
- SQLAlchemy 2.0 `select()` 스타일 (`session.query()` 사용 금지)
- Pydantic V2 문법 (`field_validator`, `model_validator`, `model_config`)
- `Annotated` 패턴으로 의존성 주입

## Import 규칙

- 레이어 참조: `from src.{layer}.{domain} import ...`
- ForeignKey는 테이블명 문자열 참조: `ForeignKey("users.id")`
- `db/__init__.py`에 모든 모델 배럴 import (새 모델 추가 시 필수)
- import 순서: 표준 라이브러리 -> 외부 패키지 -> 프로젝트 내부

## 응답 형식

```
성공: {"success": true, "data": {...}, "message": "...", "timestamp": "..."}
에러: {"success": false, "error": {"code": "E_XXX_000", "message": "..."}, "timestamp": "..."}
```

## 에러 코드 접두사

| 접두사 | 용도 |
|--------|------|
| `E_AUTH_` | 인증 |
| `E_PERM_` | 권한 |
| `E_VALID_` | 검증 |
| `E_RESOURCE_` | 리소스 미존재 (001~007) |
| `E_CONFLICT_` | 충돌 |
| `E_SERVER_` | 서버 내부 오류 |

## 페이지네이션

- 커서 기반: events, community, search
- 페이지 기반: issues, sources, tracking

## 인증 구조

- JWT HS256, Access 60분, Refresh 14일
- 권한: Public / Member (Bearer) / Admin (Bearer + admin)
- SNS 로그인: 카카오, 네이버, 구글
