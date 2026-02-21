---
title: XSS Prevention
impact: CRITICAL
category: security
tags: xss, security, html, fastapi, csp
---

# Cross-Site Scripting (XSS) Prevention

사용자 입력을 HTML에 삽입할 때 반드시 이스케이프 또는 새니타이징을 수행해야 합니다. 백엔드 API에서도 적절한 보안 헤더와 응답 처리가 필요합니다.

## Why This Matters

XSS는 공격자가 다른 사용자가 보는 웹 페이지에 악성 스크립트를 삽입할 수 있게 합니다:
- **세션 탈취**: 쿠키/토큰 도용
- **자격 증명 도용**: 키로깅, 폼 하이재킹
- **피싱 공격**: 신뢰할 수 있는 사이트 위장
- **악성코드 배포**: 사용자 브라우저에서 실행

## FastAPI 백엔드 관점

### JSONResponse는 기본적으로 안전

FastAPI의 기본 응답 방식은 JSON 직렬화를 수행하므로 XSS에 대해 본질적으로 안전합니다:

```python
# ✅ 안전: JSONResponse는 자동으로 JSON 직렬화
@router.get("/users/{user_id}")
def get_user(user_id: int, db: DbSession):
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    db.commit()
    # JSON 직렬화로 인해 HTML 태그가 문자열로 처리됨
    return success_response(data=UserResponse.model_validate(user))

# 사용자 이름이 "<script>alert('xss')</script>"이어도
# JSON 응답에서는 문자열로 이스케이프되어 안전
```

### ❌ HTMLResponse 사용 시 위험

```python
from fastapi.responses import HTMLResponse

# ❌ 사용자 입력을 HTML에 직접 삽입
@router.get("/profile/{username}", response_class=HTMLResponse)
def get_profile_page(username: str):
    return f"<html><body><h1>Welcome, {username}</h1></body></html>"

# 공격: /profile/<script>alert('xss')</script>
# 악성 스크립트가 그대로 실행됨!
```

### ✅ HTMLResponse 안전한 사용

```python
from markupsafe import escape
from fastapi.responses import HTMLResponse

# ✅ markupsafe로 이스케이프 처리
@router.get("/profile/{username}", response_class=HTMLResponse)
def get_profile_page(username: str):
    safe_username = escape(username)
    return f"<html><body><h1>Welcome, {safe_username}</h1></body></html>"
```

### ✅ 사용자 입력에 HTML 허용이 필요한 경우

리치 텍스트 입력 등에서 HTML을 허용해야 할 때는 bleach/markupsafe를 사용합니다:

```python
import bleach

# ✅ 허용된 태그만 통과시키고 나머지는 제거
def sanitize_html_content(dirty_html: str) -> str:
    return bleach.clean(
        dirty_html,
        tags=["p", "b", "i", "strong", "em", "a", "br", "ul", "ol", "li"],
        attributes={"a": ["href", "title"]},
        strip=True,
    )

# 서비스 레이어에서 저장 전 새니타이징
class PostService:
    def create_post(self, db: Session, payload: PostCreateRequest, author_id: int) -> Post:
        post = Post(
            title=payload.title,
            content=sanitize_html_content(payload.content),  # ✅ 저장 전 새니타이징
            author_id=author_id,
        )
        db.add(post)
        db.flush()
        return post
```

### ✅ CSP 헤더 미들웨어 설정 (FastAPI)

Content Security Policy 헤더로 XSS 공격의 영향을 최소화합니다:

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 관련 HTTP 헤더를 추가하는 미들웨어"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # XSS 방지를 위한 CSP 헤더
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )

        # 추가 보안 헤더
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

# FastAPI 앱에 미들웨어 등록
app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

### ✅ CORS 설정의 보안 의미

CORS 설정이 XSS와 결합되면 공격 범위가 확대될 수 있습니다:

```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ 모든 오리진 허용 - 보안 위험
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 위험: 모든 도메인에서 요청 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 허용 오리진을 명시적으로 제한
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trendkorea.example.com",
        "https://admin.trendkorea.example.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## 프론트엔드 XSS 방지 (간략 참고)

### React (자동 이스케이프)

```jsx
// ✅ React는 기본적으로 자동 이스케이프
function UserProfile({ user }) {
  return <div>{user.bio}</div>;
}

// ❌ dangerouslySetInnerHTML 사용 시 반드시 새니타이징 필요
import DOMPurify from 'dompurify';

function UserProfile({ user }) {
  const sanitizedBio = DOMPurify.sanitize(user.bio);
  return <div dangerouslySetInnerHTML={{ __html: sanitizedBio }} />;
}
```

### Vanilla JavaScript

```javascript
// ✅ textContent로 안전하게 텍스트 삽입
element.textContent = userInput;

// ❌ innerHTML에 사용자 입력 직접 삽입 금지
element.innerHTML = userInput;  // XSS 취약점!
```

## Sanitization 라이브러리

### bleach (Python 백엔드)
```python
import bleach

clean = bleach.clean(
    dirty_html,
    tags=["p", "b", "i", "strong", "em", "a"],
    attributes={"a": ["href", "title"]},
    strip=True,
)
```

### markupsafe (Python 이스케이프)
```python
from markupsafe import escape

# HTML 특수 문자를 엔티티로 변환
safe_text = escape("<script>alert('xss')</script>")
# 결과: &lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;
```

### DOMPurify (프론트엔드)
```javascript
import DOMPurify from 'dompurify';

const clean = DOMPurify.sanitize(dirty, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
  ALLOWED_ATTR: ['href']
});
```

## Best Practices Checklist

- [ ] **JSONResponse 기본 사용**: HTML 응답은 가능한 한 피하기
- [ ] **HTMLResponse 사용 시 이스케이프 필수**: `markupsafe.escape()` 적용
- [ ] **리치 텍스트 입력은 bleach로 새니타이징**: 저장 전 반드시 처리
- [ ] **CSP 헤더 설정**: `SecurityHeadersMiddleware` 적용
- [ ] **CORS 오리진 제한**: `allow_origins=["*"]` 금지
- [ ] **X-Content-Type-Options: nosniff** 헤더 추가
- [ ] **HTTPOnly 쿠키 사용**: JavaScript에서 쿠키 접근 차단
- [ ] **프론트엔드에서도 이스케이프**: React 자동 이스케이프 활용, `dangerouslySetInnerHTML` 지양

## References

- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Content Security Policy (CSP)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [bleach Documentation](https://bleach.readthedocs.io/)
- [markupsafe Documentation](https://markupsafe.palletsprojects.com/)
