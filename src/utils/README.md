# utils

`src/utils`는 수집/요약/파이프라인 실행과 보조 유틸리티를 모아둔 폴더입니다.

## 하위 모듈
- `keyword_crawler`: 뉴스 채널 헤드라인 기반 키워드 추출
- `news_crawler`: 외부 news-pipeline 호출 래퍼
- `naver_news_crawler`: 네이버 뉴스 검색 API 수집
- `news_summarizer`: LLM(Ollama) 기반 키워드별 요약
- `pipeline`: 전체 파이프라인 오케스트레이터
- `product_crawler`: 생필품 가격 API 수집
- `social`: 소셜 로그인 Provider 공통 인터페이스/레지스트리

## CLI 엔트리포인트
- `uv run trend-korea-crawl-keywords`
- `uv run trend-korea-crawl-news`
- `uv run trend-korea-crawl-naver-news`
- `uv run trend-korea-summarize-news`
- `uv run trend-korea-full-cycle`
- `uv run trend-korea-crawl-products`

## 참고
각 모듈 상세는 해당 폴더의 `README.md`를 참고하세요.
