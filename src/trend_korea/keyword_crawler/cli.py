from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from trend_korea.keyword_crawler.crawler import run_crawl, save_to_db


def main() -> None:
    parser = argparse.ArgumentParser(
        description="뉴스 채널 메인 페이지에서 주요 키워드를 추출합니다",
    )
    parser.add_argument("--top-n", type=int, default=30, help="통합 키워드 수 (default: 30)")
    parser.add_argument("--per-channel", type=int, default=20, help="채널별 키워드 수 (default: 20)")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP 타임아웃 초 (default: 15)")
    parser.add_argument(
        "--category", choices=["broadcast", "newspaper"], default=None,
        help="채널 카테고리 필터",
    )
    parser.add_argument("--out", default=None, help="출력 파일 경로 (default: stdout)")
    parser.add_argument("--pretty", action="store_true", help="JSON 들여쓰기")
    parser.add_argument("--save-db", action="store_true", help="결과를 DB에 저장")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    result = run_crawl(
        top_n_per_channel=args.per_channel,
        top_n_aggregated=args.top_n,
        timeout=args.timeout,
        category_filter=args.category,
    )

    # DB 저장
    if args.save_db:
        saved = save_to_db(result)
        print(f"[DB] {saved}건 저장 완료")

    # JSON 출력
    indent = 2 if args.pretty else None
    json_str = json.dumps(result.to_dict(), ensure_ascii=False, indent=indent)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json_str, encoding="utf-8")
        print(
            f"[완료] {result.successful_channels}/{result.total_channels} 채널 성공, "
            f"통합 키워드 {len(result.aggregated_keywords)}개 → {args.out}"
        )
    else:
        if not args.save_db:
            print(json_str)
        else:
            print(
                f"[완료] {result.successful_channels}/{result.total_channels} 채널 성공, "
                f"통합 키워드 {len(result.aggregated_keywords)}개"
            )

    sys.exit(0 if result.successful_channels > 0 else 1)


if __name__ == "__main__":
    main()
