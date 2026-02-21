---
title: Authentication & Authorization Review
impact: CRITICAL
category: security
tags: jwt, auth, rbac, authorization, authentication
---

# Authentication & Authorization Review

JWT 검증 및 역할 기반 접근 제어(RBAC)가 올바르게 구현되었는지 확인합니다.

## Why This Matters

인증/인가 결함은 가장 심각한 보안 취약점 중 하나입니다:
- **데이터 유출**: 인증되지 않은 사용자가 민감한 데이터에 접근
- **권한 상승**: 일반 사용자가 관리자 기능을 실행
- **세션 탈취**: 토큰 검증 미흡으로 인한 위조 토큰 수용
- **OWASP Top 10**: Broken Access Control은 2021년 기준 1위 취약점

## ❌ Incorrect

### 1. 인증 의존성 누락

보호가 필요한 엔드포인트에 인증 의존성을 사용하지 않는 경우:

```python
# ❌ 인증 없이 사용자 정보 조회 가능
@router.get("/users/me")
def get_my_profile(db: DbSession):
    # 누구든 접근 가능!
    return success_response(data={"message": "프로필"})
```

### 2. 권한 수준 불일치

관리자 전용 기능에 낮은 권한 의존성을 사용하는 경우:

```python
# ❌ 관리자 전용 기능에 일반 회원 권한 사용
@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user_id: CurrentMemberUserId,  # 관리자 권한이어야 함!
    db: DbSession,
):
    db.execute(delete(User).where(User.id == user_id))
    db.commit()
    return success_response(message="사용자 삭제 완료")
```

### 3. JWT 토큰 타입 미검증

refresh 토큰을 access 토큰으로 사용할 수 있는 경우:

```python
# ❌ 토큰 타입을 검증하지 않음
def get_current_user_id(token: str) -> int:
    payload = decode_token(token)
    # payload.get("typ") 검증 없이 바로 사용자 ID 반환
    return payload.get("sub")
```

### 4. request.state 직접 접근

의존성 시스템을 우회하여 request.state에 직접 접근하는 경우:

```python
# ❌ 의존성 주입을 우회하여 직접 접근
@router.get("/protected")
def protected_endpoint(request: Request, db: DbSession):
    user_id = request.state.user_id  # 미들웨어에 의존, 의존성 체계 우회
    return success_response(data={"user_id": user_id})
```

## ✅ Correct

### 1. 적절한 의존성 사용

역할에 맞는 Annotated 의존성 패턴을 사용합니다:

```python
# ✅ 일반 인증 사용자 (로그인한 모든 사용자)
@router.get("/users/me")
def get_my_profile(
    current_user_id: CurrentUserId,
    db: DbSession,
):
    stmt = select(User).where(User.id == current_user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise AppError(code="E_AUTH_002", message="사용자를 찾을 수 없습니다", status_code=401)
    db.commit()
    return success_response(data=UserResponse.model_validate(user))

# ✅ 회원 이상 권한 (member + admin)
@router.post("/posts")
def create_post(
    payload: PostCreateRequest,
    current_user_id: CurrentMemberUserId,
    db: DbSession,
):
    post = Post(title=payload.title, content=payload.content, author_id=current_user_id)
    db.add(post)
    db.commit()
    return success_response(data=PostResponse.model_validate(post))

# ✅ 관리자 전용 기능
@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user_id: CurrentAdminUserId,
    db: DbSession,
):
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise AppError(code="E_AUTH_002", message="사용자를 찾을 수 없습니다", status_code=401)
    db.delete(user)
    db.commit()
    return success_response(message="사용자 삭제 완료")
```

### 2. 토큰 타입 검증

access/refresh 토큰을 구분하여 검증합니다:

```python
# ✅ 토큰 타입 검증 포함
def get_current_user_id(token: str) -> int:
    payload: TokenPayload = decode_token(token)

    if payload.get("typ") != "access":
        raise AppError(
            code="E_AUTH_003",
            message="유효하지 않은 토큰 타입입니다",
            status_code=401,
        )

    user_id = payload.get("sub")
    if not user_id:
        raise AppError(
            code="E_AUTH_001",
            message="인증 토큰이 없습니다",
            status_code=401,
        )
    return int(user_id)
```

### 3. AppError 코드 체계

일관된 에러 코드를 사용합니다:

```python
# ✅ 인증 관련 에러 코드 체계
# E_AUTH_001: 토큰 누락
raise AppError(code="E_AUTH_001", message="인증 토큰이 없습니다", status_code=401)

# E_AUTH_002: 사용자 미존재
raise AppError(code="E_AUTH_002", message="사용자를 찾을 수 없습니다", status_code=401)

# E_AUTH_003: 유효하지 않은 토큰
raise AppError(code="E_AUTH_003", message="유효하지 않은 토큰 타입입니다", status_code=401)

# ✅ 권한 관련 에러 코드 체계
# E_PERM_001: 기능 접근 권한 없음
raise AppError(code="E_PERM_001", message="해당 기능에 대한 권한이 없습니다", status_code=403)

# E_PERM_002: 리소스 접근 권한 없음
raise AppError(code="E_PERM_002", message="해당 리소스에 대한 권한이 없습니다", status_code=403)
```

## Checklist

- [ ] **모든 보호 엔드포인트에 인증 의존성 사용**: `CurrentUserId`, `CurrentMemberUserId`, `CurrentAdminUserId`
- [ ] **역할별 적절한 의존성 선택**: 관리자 기능에는 `CurrentAdminUserId` 사용
- [ ] **JWT 토큰 타입 검증**: `payload.get("typ") == "access"` 확인
- [ ] **request.state 직접 접근 금지**: 항상 Annotated 의존성 패턴 사용
- [ ] **일관된 AppError 코드 사용**: `E_AUTH_*` (인증), `E_PERM_*` (권한)
- [ ] **리소스 소유권 검증**: 본인 리소스만 수정/삭제 가능하도록 확인
- [ ] **토큰 만료 처리**: 만료된 토큰에 대한 적절한 에러 응답
- [ ] **비밀번호 해싱**: `CryptContext(schemes=["bcrypt"])` 사용
- [ ] **토큰 생성/검증 로직 분리**: `python-jose`를 통한 JWT 처리

## References

- [OWASP Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
