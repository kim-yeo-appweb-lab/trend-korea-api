# news_crawler

외부 `news-crawl-pipeline` 프로젝트를 subprocess로 호출해 키워드별 뉴스를 수집합니다.

## 주요 파일
- `crawler.py`: `uv run news-pipeline` 호출 래퍼
- `cli.py`: CLI 진입점

## 실행
```bash
uv run trend-korea-crawl-news --keyword "트럼프" --keyword "관세" --limit 3
```

## 필수 설정
- `NEWS_PIPELINE_DIR`: 외부 파이프라인 디렉토리 경로

## 출력
- 기사 JSON 파일 (`--out`)
- 크롤 리포트 JSON (`--report-out`, 선택)

## 비고
- 외부 프로젝트 실행 실패 시 `RuntimeError`를 발생시킵니다.
