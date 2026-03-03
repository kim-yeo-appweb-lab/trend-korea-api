from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from src.utils.naver_news_crawler.fetcher import run_fetch, save_to_db


def main() -> None:
    parser = argparse.ArgumentParser(
        description="네이버 뉴스 검색 API로 키워드별 뉴스를 수집합니다",
    )
    parser.add_argument("keywords", nargs="+", help="검색 키워드 (공백 구분, 여러 개 가능)")
    parser.add_argument(
        "--display", type=int, default=100, help="페이지당 건수, 최대 100 (default: 100)"
    )
    parser.add_argument("--max-start", type=int, default=1000, help="최대 start 값 (default: 1000)")
    parser.add_argument(
        "--sort",
        choices=["date", "sim"],
        default="date",
        help="정렬: date=날짜순, sim=정확도순 (default: date)",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="HTTP 타임아웃 초 (default: 10)"
    )
    parser.add_argument("--out", default=None, help="JSON 출력 파일 경로 (default: stdout)")
    parser.add_argument("--pretty", action="store_true", help="JSON 들여쓰기")
    parser.add_argument("--save-db", action="store_true", help="결과를 DB에 저장")
    args = parser.parse_args()

    log = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        result = run_fetch(
            keywords=args.keywords,
            display=args.display,
            max_start=args.max_start,
            sort=args.sort,
            timeout=args.timeout,
        )
    except Exception as exc:
        log.error("수집 실패: %s", exc)
        sys.exit(1)

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
        print(f"[완료] {len(result.keywords)}개 키워드, {result.total_articles}건 → {args.out}")
    else:
        if not args.save_db:
            print(json_str)
        else:
            print(
                f"[완료] {len(result.keywords)}개 키워드, "
                f"{result.total_articles}건 수집 ({result.elapsed_seconds}초)"
            )

    sys.exit(0 if result.total_articles > 0 else 1)


if __name__ == "__main__":
    main()
