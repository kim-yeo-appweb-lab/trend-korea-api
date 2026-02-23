# 파이프라인 모듈 구조

> 2026-02-23 리팩터링: 분산된 파이프라인 코드를 `src/utils/` 폴더 단위로 재구조화

## 배경

키워드 크롤링, 뉴스 크롤링, 뉴스 요약 로직이 여러 위치에 분산되어 있었음:

| 변경 전 | 문제점 |
|---------|--------|
| `src/keyword_crawler/` | 최상위 패키지로 분리되어 있어 `src/utils/` 컨벤션과 불일치 |
| `scripts/summarize_news.py` (420줄) | 단일 스크립트, `dotenv` + `sys.path.insert` 해킹 |
| `scripts/run_full_cycle.py` | 모든 단계를 subprocess로 호출, 하드코딩된 경로 |

## 최종 구조

```
src/utils/
├── __init__.py
├── dependencies.py              # 기존 (변경 없음)
├── error_handlers.py            # 기존 (변경 없음)
├── social/                      # 기존 (변경 없음)
├── keyword_crawler/             # ← src/keyword_crawler/ 에서 이동
│   ├── __init__.py              # barrel exports
│   ├── cli.py                   # CLI 진입점
│   ├── crawler.py               # 비동기 크롤링 + DB 저장
│   ├── headline_extractor.py    # 채널별 헤드라인 추출
│   ├── http_client.py           # 비동기 HTTP 클라이언트
│   └── keyword_analyzer.py      # kiwipiepy 형태소 분석 키워드 추출
├── news_crawler/                # ← 신규 (외부 파이프라인 래퍼)
│   ├── __init__.py
│   ├── cli.py                   # --keyword, --limit CLI
│   └── crawler.py               # subprocess 래퍼, settings 기반 경로
├── news_summarizer/             # ← scripts/summarize_news.py 분할
│   ├── __init__.py
│   ├── cli.py                   # --input, --model, --save-db CLI
│   ├── llm_client.py            # Ollama OpenAI-compatible 클라이언트
│   ├── prompt_builder.py        # 기사 로드, 그룹핑, 프롬프트 구성
│   └── summarizer.py            # 요약 실행, JSON 파싱, 매칭, DB 저장
└── pipeline/                    # ← scripts/run_full_cycle.py 리팩터링
    ├── __init__.py
    ├── cli.py                   # --repeat, --top-n, --max-keywords CLI
    └── orchestrator.py          # 직접 함수 호출 + subprocess 혼합 오케스트레이터
```

## CLI 진입점

```bash
# 키워드 크롤러 (경로 변경)
uv run trend-korea-crawl-keywords --top-n 30 --save-db

# 뉴스 크롤링 (신규)
uv run trend-korea-crawl-news --keyword "트럼프" --keyword "관세" --limit 3

# 뉴스 요약 (신규)
uv run trend-korea-summarize-news --input news.json --model gemma3:4b --save-db

# 전체 파이프라인 (신규)
uv run trend-korea-full-cycle --repeat 3 --max-keywords 5 --limit 3
```

## 환경변수

`src/core/config.py`의 `Settings` 클래스에 3개 필드 추가:

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama LLM 서버 URL |
| `OLLAMA_DEFAULT_MODEL` | `gemma3:4b` | 기본 요약 모델 |
| `NEWS_PIPELINE_DIR` | (빈 문자열) | 외부 news-crawl-pipeline 프로젝트 경로 |

## 의존성

```toml
[project.optional-dependencies]
crawler = ["httpx", "beautifulsoup4", "lxml", "kiwipiepy"]
summarizer = ["openai>=1.0.0,<2.0.0", "python-dotenv>=1.0.0,<2.0.0"]
```

설치: `uv sync --extra crawler --extra summarizer`

## 설계 결정

### 직접 함수 호출 vs subprocess

- **keyword_crawler**: 직접 호출 (같은 Python 프로세스)
- **news_crawler**: subprocess 호출 (외부 프로젝트, 별도 virtualenv)
- **news_summarizer**: 직접 호출 (같은 Python 프로세스)

직접 호출 시 kiwipiepy 모델 로드가 1회만 발생하여 반복 실행 시 성능 향상.

### dotenv 제거

기존 `scripts/summarize_news.py`의 `dotenv` + `sys.path.insert` 해킹을 제거하고
`pydantic-settings` 기반 `get_settings()`로 통합. `.env` 파일은 pydantic-settings가
자동으로 읽음.

## 검증 결과 (2026-02-23)

3회 사이클 테스트 결과:

| 지표 | 값 |
|------|-----|
| 성공/실패 | 3/0 |
| 평균 소요 시간 | 41.4초/사이클 |
| 총 기사 | 54건 |
| 총 요약 | 6건 |
| 총 태그 | 30개 |
| 키워드 매핑 성공률 | 100% (6/6) |
