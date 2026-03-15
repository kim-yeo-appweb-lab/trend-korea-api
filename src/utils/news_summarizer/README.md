# news_summarizer

수집된 뉴스 기사(JSON/JSONL)를 키워드별로 묶어 LLM(Ollama)으로 요약합니다.

## 주요 파일
- `summarizer.py`: 요약 실행, JSON 파싱/정규화, 키워드 매핑, DB 저장
- `prompt_builder.py`: 기사 로드/그룹핑/프롬프트 생성
- `llm_client.py`: Ollama(OpenAI-compatible) 클라이언트
- `cli.py`: CLI 진입점

## 실행
```bash
uv run trend-korea-summarize-news --input news_crawl_results.json --save-db
```

## 설정
- `OLLAMA_BASE_URL` (기본: `http://localhost:11434/v1`)
- `OLLAMA_DEFAULT_MODEL` (기본: `gemma3:4b`)

## 출력
- 요약 JSON 파일 (`*_summaries.json`)
- 옵션 시 DB 저장:
  - `news_summary_batches`
  - `news_keyword_summaries`
  - `news_summary_tags`
