# keyword_crawler

뉴스 채널(RSS/HTML)에서 헤드라인을 수집하고, 형태소 분석 기반 키워드를 추출합니다.

## 주요 파일
- `crawler.py`: 채널 조회, 비동기 수집, 키워드/교집합 계산, DB 저장
- `headline_extractor.py`: 채널별 헤드라인 추출 규칙
- `http_client.py`: async HTTP 클라이언트(재시도/백오프)
- `keyword_analyzer.py`: `kiwipiepy` 기반 명사구 키워드 추출
- `cli.py`: CLI 진입점

## 실행
```bash
uv run trend-korea-crawl-keywords --top-n 30 --per-channel 20 --save-db
```

## 출력
- JSON 결과: 채널별 키워드, 통합 키워드, 교집합 키워드
- 옵션 시 DB 저장: `crawled_keywords`, `keyword_intersections`

## 의존성
- optional extra: `crawler` (`httpx`, `beautifulsoup4`, `lxml`, `kiwipiepy`)
