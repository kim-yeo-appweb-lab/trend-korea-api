## 브랜칭 전략

GitHub Flow 기반. `main`은 항상 배포 가능 상태 유지.

### 브랜치 명명 규칙

```
<타입>/<설명>
```

| 타입        | 용도           | 예시                          |
| ----------- | -------------- | ----------------------------- |
| `feature/`  | 새 기능        | `feature/user-authentication` |
| `fix/`      | 버그 수정      | `fix/login-validation-error`  |
| `hotfix/`   | 긴급 수정      | `hotfix/critical-api-error`   |
| `refactor/` | 코드 개선      | `refactor/event-service`      |
| `docs/`     | 문서 작업      | `docs/api-endpoint-guide`     |
| `chore/`    | 설정/도구 변경 | `chore/update-eslint-config`  |

- 영문 소문자 + 하이픈만 사용 (50자 이내)
- 검증 정규식: `^(main|develop|(feature|fix|hotfix|refactor|docs|chore)\/[a-z0-9]([a-z0-9-]*[a-z0-9])?)$`

### 필수 규칙

- main 직접 커밋 금지 — 작업 브랜치 → PR → 병합
- 커밋 메시지: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`)
- 병합 전 CI 통과 필수
