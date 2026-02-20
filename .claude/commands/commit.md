# Commit

변경사항을 분석하여 Conventional Commits 형식으로 커밋을 생성한다.

## 절차

1. `git status`와 `git diff`로 변경사항 확인
2. 변경사항을 논리적 단위로 분리 (레이어별: domain → infrastructure → application → api)
3. 각 단위별로 커밋 생성

## 커밋 메시지 형식

```
{type}({scope}): {subject}

{body}
```

### 타입

- `feat` - 새로운 기능
- `fix` - 버그 수정
- `refactor` - 코드 리팩토링
- `style` - 코드 포맷팅 (동작 변경 없음)
- `docs` - 문서 변경
- `test` - 테스트 추가/수정
- `chore` - 빌드, 설정, Docker, CI 변경
- `perf` - 성능 개선
- `migration` - Alembic 마이그레이션

### 스코프 (선택)

- `domain` - 도메인 모델, 엔티티, 리포지토리 인터페이스
- `infra` - SQLAlchemy 구현체, 외부 서비스 연동
- `app` - 유스케이스, 서비스 레이어
- `api` - FastAPI 라우터, 스키마, 의존성
- `crawler` - 키워드 크롤러
- `worker` - 스케줄러, 백그라운드 작업
- `config` - 설정, 환경변수, pyproject.toml

### 규칙

- 제목은 한국어, 50자 이내
- 이모지 사용 금지
- 한꺼번에 커밋하지 않고 작은 작업 단위로 분리
- body는 선택사항이며, 필요시 "왜" 변경했는지 설명
- .env 파일은 절대 커밋하지 않음 (.env.example만 커밋)
- 커밋 후 `git status`로 결과 확인