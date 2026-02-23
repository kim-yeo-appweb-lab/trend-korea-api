"""뉴스 크롤링 CLI.

Usage:
    uv run trend-korea-crawl-news --keyword "트럼프" --keyword "관세" --limit 3
    uv run trend-korea-crawl-news --keyword "AI" --out /tmp/news.json --pipeline-dir /path/to/pipeline
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="외부 뉴스 파이프라인으로 키워드별 뉴스 수집")
    parser.add_argument(
        "--keyword", action="append", required=True, help="크롤링 키워드 (여러 개 가능)"
    )
    parser.add_argument("--limit", type=int, default=3, help="키워드/채널당 기사 수 (기본: 3)")
    parser.add_argument("--out", default=None, help="출력 JSON 경로 (기본: news_crawl_results.json)")
    parser.add_argument("--report-out", default=None, help="크롤 리포트 JSON 경로")
    parser.add_argument("--pipeline-dir", default=None, help="외부 파이프라인 디렉토리 경로")
    args = parser.parse_args()

    from src.utils.news_crawler.crawler import run_news_crawl

    out_path = args.out or "news_crawl_results.json"

    try:
        articles = run_news_crawl(
            keywords=args.keyword,
            output_path=out_path,
            report_path=args.report_out,
            limit=args.limit,
            pipeline_dir=args.pipeline_dir,
        )
        print(f"\n[완료] {len(articles)}건 수집 → {out_path}")
        if args.report_out:
            print(f"  리포트: {args.report_out}")
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
