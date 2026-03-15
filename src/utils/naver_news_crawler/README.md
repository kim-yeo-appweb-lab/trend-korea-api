# naver_news_crawler

네이버 뉴스 검색 API로 키워드별 뉴스 메타데이터를 수집합니다.

## 주요 파일
- `fetcher.py`: API 호출, 페이지네이션, 결과 변환, DB 저장
- `cli.py`: CLI 진입점

## 실행
```bash
uv run trend-korea-crawl-naver-news "트럼프" "관세" --display 20 --max-start 100
```

## 필수 설정
- `NAVER_API_CLIENT`
- `NAVER_API_CLIENT_SECRET`

## 출력
- 수집 결과 JSON (`FetchResult`)
- 옵션 시 DB 저장: `naver_news_articles`
- 파이프라인 연동용 변환 함수: `to_article_dicts()`
