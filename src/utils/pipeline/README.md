# pipeline

키워드 수집 -> 뉴스 수집 -> 네이버 보강 -> 요약까지 전체 사이클을 실행하는 오케스트레이터입니다.

## 주요 파일
- `orchestrator.py`: 사이클 실행/반복 실행/결과 저장
- `cli.py`: CLI 진입점

## 실행
```bash
uv run trend-korea-full-cycle --repeat 3 --top-n 30 --max-keywords 5 --limit 3
```

## 핵심 옵션
- `--keyword-strategy intersection|aggregated`
- `--no-naver`
- `--model <ollama_model>`

## 출력
- `cycle_outputs/run_<timestamp>/cycle_##/`
  - `keywords.json`
  - `crawl.json`
  - `crawl_report.json`
  - `summary.json`
- 런 전체 요약 메타데이터 JSON
