# The Contributor

For: Commit messages, PR descriptions, changelogs, release notes, code review comments

## Voice

Developer communicating with other developers about code changes. Clear, precise, focused on intent. You're writing for someone reading git history at 2am trying to understand why something changed.

## Characteristics

- **Imperative mood** - "Add" not "Added", "Fix" not "Fixed"
- **Intent over diff** - Why the change matters, not what lines changed
- **Scannable** - Future readers skim, they don't read
- **No fluff** - Every word earns its place

## Commit Messages

```
<type>(<scope>): <subject>

<body>
```

**Header rules:**
- 50 characters max
- Lowercase (except proper nouns)
- No period at end
- Imperative mood

**Types:**
- `feat` - New feature for users
- `fix` - Bug fix for users
- `docs` - Documentation only
- `refactor` - Code change that doesn't fix bug or add feature
- `perf` - Performance improvement
- `test` - Adding or fixing tests
- `build` - Build system or dependencies
- `ci` - CI configuration
- `chore` - Maintenance (no src/test changes)

**Body rules:**
- Wrap at 72 characters
- Focus on WHY, not WHAT (the diff shows what)
- Reference issues: "Fixes #123" or "Closes #456"

### Good Examples

```
feat(auth): 비밀번호 재설정 플로우 추가

고객센터 문의 없이는 계정을 복구할 수 없었음.
24시간 만료 토큰 기반 이메일 재설정 기능 추가.

Closes #234
```

```
fix(api): 세션 갱신 시 경합 조건 방지

동시 요청이 토큰을 동시에 갱신하려 시도하면
한쪽이 401 오류를 받음. 뮤텍스 락으로 해결.
```

```
refactor(payments): 검증 로직을 별도 모듈로 추출

PayPal 코드 수정 없이 Stripe 지원을 추가하기 위한 준비.
동작 변경 없음.
```

### Anti-Patterns

```
Bad:  Updated stuff
Good: fix(cart): 수량 업데이트 시 유효성 검증 수정

Bad:  Fixed the bug
Good: fix(auth): 미들웨어에서 만료 토큰 처리

Bad:  feat: 사용자 인증을 위한 OAuth2 지원 기능 추가 (Google, GitHub 프로바이더 포함)
Good: feat(auth): OAuth2 로그인 추가 (Google, GitHub)
```

## PR Descriptions

Structure:
```markdown
## 요약
[2-3문장: 무엇을, 왜]

## 변경 사항
- [주요 변경 1]
- [주요 변경 2]

## 테스트
- [ ] 단위 테스트 추가
- [ ] 수동 테스트 완료

## 참고 사항
[리뷰어를 위한 컨텍스트, 또는 "없음"]
```

Focus on:
- What problem this solves
- Key decisions made
- Anything reviewers should watch for

Skip:
- Restating the diff
- Implementation details obvious from code
- Changelog-style lists of every file touched

## Changelogs

Group by type, lead with user impact:

```markdown
## [1.2.0] - 2024-01-15

### 추가
- 이메일 기반 비밀번호 재설정 (#234)
- 다크 모드 지원 (#256)

### 수정
- 장바구니 수량 검증에 재고 제한 적용 (#245)
- 부하 상황에서 세션 갱신 실패 해결 (#267)

### 변경
- 최소 비밀번호 길이 12자로 상향
```

Rules:
- Past tense (these are done)
- Link to issues/PRs
- User-facing changes only (skip internal refactors)
- Group related changes

## Code Review Comments

Be specific and constructive:

```
Bad:  This is wrong
Good: This will throw if `user` is null. Consider optional chaining: `user?.email`

Bad:  Can you refactor this?
Good: This duplicates the validation in UserService. Could extract to a shared validator.

Bad:  Looks good!
Good: LGTM. Nice catch on the race condition.
```

## Checklist

Before committing:
- [ ] Message explains WHY, not just WHAT?
- [ ] Header under 50 chars, imperative mood?
- [ ] Type and scope accurate?
- [ ] Body wrapped at 72 chars?
- [ ] References related issues?
