# product_crawler

한국소비자원 생필품 가격 API를 호출해 상품/가격 데이터를 수집합니다.

## 주요 파일
- `fetcher.py`: 상품/가격 수집, XML/JSON 파싱, DB 저장
- `cli.py`: CLI 진입점

## 실행
```bash
uv run trend-korea-crawl-products --num-of-rows 100 --max-pages 3 --save-db
```

## 필수 설정
- `OPENAPI_PRODUCT_PRICE_ENCODING_KEY`
- `OPENAPI_PRODUCT_PRICE_ENDPOINT`

## 출력
- 수집 결과 JSON (`FetchResult`)
- 옵션 시 DB 저장:
  - `product_info`
  - `product_price`
