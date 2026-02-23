"""뉴스 요약 CLI.

Usage:
    uv run trend-korea-summarize-news --input news_crawl_results.json
    uv run trend-korea-summarize-news --input results.json --model llama3:8b
    uv run trend-korea-summarize-news --input results.json --save-db
"""

from __future__ import annotations

import argparse

from src.utils.news_summarizer.summarizer import run_summarize, save_to_db


def main() -> None:
    parser = argparse.ArgumentParser(
        description="뉴스 크롤링 결과를 Ollama LLM으로 키워드별 요약 (1회 통합 요청)"
    )
    parser.add_argument("--input", required=True, help="뉴스 크롤링 결과 JSON/JSONL 파일 경로")
    parser.add_argument("--out", default=None, help="출력 JSON 파일 경로")
    parser.add_argument("--model", default=None, help="Ollama 모델명 (기본: settings 값)")
    parser.add_argument("--save-db", action="store_true", help="요약 결과를 PostgreSQL에 저장")
    parser.add_argument("--db-url", default=None, help="DB URL (미지정 시 .env의 DATABASE_URL 사용)")
    args = parser.parse_args()

    out_file = args.out or args.input.replace(".json", "_summaries.json").replace(
        ".jsonl", "_summaries.json"
    )

    result = run_summarize(args.input, out_file, args.model)

    tokens = result["total_tokens"]
    print(f"\n[DONE] {result['total_keywords']}개 키워드 요약 완료 (API 호출: {result['api_calls']}회)")
    print(f"  모델: {result['model']}")
    print(f"  총 토큰: {tokens['total']} (prompt: {tokens['prompt']}, completion: {tokens['completion']})")
    print(f"  출력: {out_file}")

    if args.save_db:
        save_to_db(result, db_url=args.db_url)


if __name__ == "__main__":
    main()
