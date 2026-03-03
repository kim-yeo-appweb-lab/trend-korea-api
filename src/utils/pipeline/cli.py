"""전체 파이프라인 CLI.

Usage:
    uv run trend-korea-full-cycle                    # 10회 반복
    uv run trend-korea-full-cycle --repeat 5         # 5회 반복
    uv run trend-korea-full-cycle --top-n 10         # 키워드 10개
    uv run trend-korea-full-cycle --max-keywords 3   # 요약 시 키워드 3개만 사용
"""

from __future__ import annotations

import argparse

from src.utils.pipeline.orchestrator import (
    DEFAULT_LIMIT,
    DEFAULT_MAX_KEYWORDS,
    DEFAULT_REPEAT,
    DEFAULT_TOP_N,
    run_full_pipeline,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="전체 파이프라인 반복 실행")
    parser.add_argument(
        "--repeat",
        type=int,
        default=DEFAULT_REPEAT,
        help=f"반복 횟수 (기본: {DEFAULT_REPEAT})",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"키워드 추출 수 (기본: {DEFAULT_TOP_N})",
    )
    parser.add_argument(
        "--max-keywords",
        type=int,
        default=DEFAULT_MAX_KEYWORDS,
        help=f"뉴스 크롤링에 사용할 키워드 수 (기본: {DEFAULT_MAX_KEYWORDS})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"키워드/채널당 기사 수 (기본: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Ollama 모델명 (기본: settings 값)",
    )
    parser.add_argument(
        "--keyword-strategy",
        choices=["intersection", "aggregated"],
        default="intersection",
        help="키워드 선별 전략: intersection=교집합 우선, aggregated=빈도순 (기본: intersection)",
    )
    parser.add_argument(
        "--no-naver",
        action="store_true",
        help="네이버 뉴스 검색 비활성화",
    )
    parser.add_argument(
        "--no-classify",
        action="store_true",
        help="기사 분류/중복 제거 비활성화",
    )
    args = parser.parse_args()

    run_full_pipeline(
        repeat=args.repeat,
        top_n=args.top_n,
        max_keywords=args.max_keywords,
        limit=args.limit,
        model=args.model,
        use_naver=not args.no_naver,
        keyword_strategy=args.keyword_strategy,
        enable_classification=not args.no_classify,
    )


if __name__ == "__main__":
    main()
