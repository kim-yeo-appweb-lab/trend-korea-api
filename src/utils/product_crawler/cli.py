from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from src.utils.product_crawler.fetcher import run_fetch, save_to_db


def main() -> None:
    parser = argparse.ArgumentParser(
        description="한국소비자원 생필품 가격 정보를 수집합니다",
    )
    parser.add_argument("--num-of-rows", type=int, default=100, help="페이지당 건수 (default: 100)")
    parser.add_argument(
        "--max-pages", type=int, default=None, help="최대 페이지 수 (default: 전체)"
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="HTTP 타임아웃 초 (default: 30)"
    )
    parser.add_argument("--out", default=None, help="JSON 출력 파일 경로 (default: stdout)")
    parser.add_argument("--pretty", action="store_true", help="JSON 들여쓰기")
    parser.add_argument("--save-db", action="store_true", help="결과를 DB에 저장")
    parser.add_argument(
        "--products-only", action="store_true", help="상품 정보만 수집 (가격 조회 생략)"
    )
    args = parser.parse_args()

    log = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        result = run_fetch(
            num_of_rows=args.num_of_rows,
            max_pages=args.max_pages,
            timeout=args.timeout,
            products_only=args.products_only,
        )
    except Exception as exc:
        log.error("수집 실패: %s", exc)
        sys.exit(1)

    # DB 저장
    if args.save_db:
        prod_saved, price_saved = save_to_db(result)
        print(f"[DB] 상품 {prod_saved}건, 가격 {price_saved}건 저장 완료")

    # JSON 출력
    indent = 2 if args.pretty else None
    json_str = json.dumps(result.to_dict(), ensure_ascii=False, indent=indent)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json_str, encoding="utf-8")
        print(f"[완료] 상품 {result.product_count}건, 가격 {result.price_count}건 → {args.out}")
    else:
        if not args.save_db:
            print(json_str)
        else:
            print(
                f"[완료] 상품 {result.product_count}건, "
                f"가격 {result.price_count}건 수집 ({result.elapsed_seconds}초)"
            )

    sys.exit(0 if result.product_count > 0 else 1)


if __name__ == "__main__":
    main()
