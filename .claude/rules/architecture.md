## 진입점

| 명령어 | 진입점 |
|--------|--------|
| `trend-korea-api` | `src/main.py:run` |
| `trend-korea-worker` | `src/worker_main.py:run` |
| `trend-korea-crawl-keywords` | `src/utils/keyword_crawler/cli.py:main` |
| `trend-korea-crawl-news` | `src/utils/news_crawler/cli.py:main` |
| `trend-korea-crawl-naver-news` | `src/utils/naver_news_crawler/cli.py:main` |
| `trend-korea-summarize-news` | `src/utils/news_summarizer/cli.py:main` |
| `trend-korea-crawl-products` | `src/utils/product_crawler/cli.py:main` |
| `trend-korea-full-cycle` | `src/utils/pipeline/cli.py:main` |

## 디렉터리 구조

```
src/
├── main.py            # FastAPI 앱 진입점
├── worker_main.py     # APScheduler 워커 진입점
├── api/v1/            # 라우터
├── models/            # SQLAlchemy 2.0 모델
├── schemas/           # Pydantic V2 스키마
├── crud/              # 비즈니스 로직
├── sql/               # 데이터 액세스 계층
├── core/              # 설정, 보안, 예외, 로깅, 페이지네이션
├── db/                # Base 모델, 세션, enum, 배럴 import
├── utils/             # 공용 유틸리티 + 파이프라인 모듈
└── scheduler/
```

## 공유 레이어

- `core/config.py` — pydantic-settings (Settings)
- `core/security.py` — 비밀번호 해싱, JWT
- `core/exceptions.py` — AppError
- `core/response.py` — success_response
- `core/pagination.py` — 커서 기반 페이지네이션
- `db/__init__.py` — 모든 모델 배럴 import (Alembic용)
- `db/session.py` — 엔진/세션 팩토리
- `db/enums.py` — 공유 Enum
- `utils/dependencies.py` — DbSession, CurrentMemberUserId, CurrentAdminUserId
- `utils/error_handlers.py` — 글로벌 예외 핸들러
- `utils/social/` — 소셜 인증

## 스케줄러 잡

| 잡 이름 | 주기 | 설명 |
|---------|------|------|
| issue_status_reconcile | 30분 | 이슈 상태 조정 |
| search_rankings | 매시 정각 | 검색 랭킹 재계산 |
| community_hot_score | 10분 | 인기 게시글 점수 업데이트 |
| cleanup_refresh_tokens | 매일 03:00 | 만료 토큰 정리 |
