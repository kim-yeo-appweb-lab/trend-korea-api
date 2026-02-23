"""키워드 수집 → 뉴스 크롤링 → 뉴스 요약 전체 파이프라인 오케스트레이터.

keyword_crawler와 news_summarizer는 직접 함수 호출,
news_crawler만 subprocess (외부 프로젝트).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.utils.keyword_crawler.crawler import run_crawl
from src.utils.news_crawler.crawler import run_news_crawl
from src.utils.news_summarizer.summarizer import run_summarize

DEFAULT_REPEAT = 10
DEFAULT_TOP_N = 30
DEFAULT_MAX_KEYWORDS = 5
DEFAULT_LIMIT = 3


def run_cycle(
    cycle_num: int,
    cycle_dir: Path,
    top_n: int = DEFAULT_TOP_N,
    max_keywords: int = DEFAULT_MAX_KEYWORDS,
    limit: int = DEFAULT_LIMIT,
    model: str | None = None,
) -> dict:
    """한 사이클 실행. 결과 메타데이터 반환."""
    start = time.time()
    print(f"\n{'=' * 60}")
    print(f"  사이클 {cycle_num} 시작 ({datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC)")
    print(f"{'=' * 60}")

    cycle_dir.mkdir(parents=True, exist_ok=True)

    # 1. 키워드 수집 (직접 함수 호출)
    print("  [1/3] 키워드 수집 중...")
    try:
        crawl_output = run_crawl(top_n_aggregated=top_n)
    except Exception as exc:
        print(f"  [키워드] 실패: {exc}")
        return {"cycle": cycle_num, "status": "fail", "stage": "keyword", "elapsed": time.time() - start}

    if crawl_output.successful_channels == 0:
        return {"cycle": cycle_num, "status": "fail", "stage": "keyword", "elapsed": time.time() - start}

    # 키워드 결과 저장
    kw_path = cycle_dir / "keywords.json"
    kw_data = crawl_output.to_dict()
    with kw_path.open("w", encoding="utf-8") as f:
        json.dump(kw_data, f, ensure_ascii=False, indent=2)

    keywords = [kw.word for kw in crawl_output.aggregated_keywords]
    if not keywords:
        return {"cycle": cycle_num, "status": "fail", "stage": "keyword", "elapsed": time.time() - start}

    # 상위 N개 키워드만 사용
    selected = keywords[:max_keywords]
    print(f"  [키워드] {len(keywords)}개 추출, 상위 {len(selected)}개 선택: {selected}")

    # 2. 뉴스 크롤링 (subprocess — 외부 프로젝트)
    print("  [2/3] 뉴스 크롤링 중...")
    crawl_path = cycle_dir / "crawl.json"
    report_path = cycle_dir / "crawl_report.json"
    try:
        articles = run_news_crawl(
            keywords=selected,
            output_path=crawl_path,
            report_path=report_path,
            limit=limit,
        )
    except RuntimeError as exc:
        print(f"  [크롤링] 실패: {exc}")
        return {"cycle": cycle_num, "status": "fail", "stage": "crawl", "elapsed": time.time() - start}

    article_count = len(articles)
    if article_count == 0:
        return {"cycle": cycle_num, "status": "fail", "stage": "crawl", "elapsed": time.time() - start}

    # 3. 뉴스 요약 (직접 함수 호출)
    print("  [3/3] 뉴스 요약 중...")
    summary_path = cycle_dir / "summary.json"
    try:
        summary = run_summarize(str(crawl_path), str(summary_path), model)
    except Exception as exc:
        print(f"  [요약] 실패: {exc}")
        return {"cycle": cycle_num, "status": "fail", "stage": "summarize", "elapsed": time.time() - start}

    elapsed = time.time() - start
    kw_summaries = summary.get("keywords", [])
    total_tags = sum(len(kw.get("tags", [])) for kw in kw_summaries)

    result = {
        "cycle": cycle_num,
        "status": "ok",
        "elapsed": round(elapsed, 1),
        "keywords_extracted": len(keywords),
        "keywords_used": len(selected),
        "articles_collected": article_count,
        "summaries": len(kw_summaries),
        "total_tags": total_tags,
        "tokens": summary.get("total_tokens", {}),
        "model": summary.get("model", ""),
    }

    print(f"  [완료] {elapsed:.1f}초 | 기사 {article_count}건 | 요약 {len(kw_summaries)}건 | 태그 {total_tags}개")
    return result


def run_full_pipeline(
    repeat: int = DEFAULT_REPEAT,
    top_n: int = DEFAULT_TOP_N,
    max_keywords: int = DEFAULT_MAX_KEYWORDS,
    limit: int = DEFAULT_LIMIT,
    model: str | None = None,
    output_dir: Path | None = None,
) -> dict:
    """전체 파이프라인을 반복 실행한다."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if output_dir is None:
        output_dir = project_root / "cycle_outputs"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"전체 파이프라인 반복 실행 ({repeat}회)")
    print(f"  출력 디렉토리: {run_dir}")
    print(f"  설정: top_n={top_n}, max_keywords={max_keywords}, limit={limit}, model={model}")

    all_results: list[dict] = []
    total_start = time.time()

    for i in range(1, repeat + 1):
        cycle_dir = run_dir / f"cycle_{i:02d}"
        result = run_cycle(i, cycle_dir, top_n, max_keywords, limit, model)
        all_results.append(result)

    total_elapsed = time.time() - total_start

    # 전체 결과 저장
    report = {
        "run_id": timestamp,
        "total_cycles": repeat,
        "total_elapsed": round(total_elapsed, 1),
        "settings": {
            "top_n": top_n,
            "max_keywords": max_keywords,
            "limit": limit,
            "model": model,
        },
        "cycles": all_results,
        "summary": {
            "success": sum(1 for r in all_results if r["status"] == "ok"),
            "fail": sum(1 for r in all_results if r["status"] == "fail"),
            "avg_elapsed": round(
                sum(r["elapsed"] for r in all_results if r["status"] == "ok")
                / max(1, sum(1 for r in all_results if r["status"] == "ok")),
                1,
            ),
            "total_articles": sum(r.get("articles_collected", 0) for r in all_results),
            "total_summaries": sum(r.get("summaries", 0) for r in all_results),
            "total_tags": sum(r.get("total_tags", 0) for r in all_results),
        },
    }

    report_path = run_dir / "run_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 최종 출력
    s = report["summary"]
    print(f"\n{'=' * 60}")
    print(f"  전체 결과 ({repeat}회)")
    print(f"{'=' * 60}")
    print(f"  성공/실패: {s['success']}/{s['fail']}")
    print(f"  총 소요 시간: {total_elapsed:.0f}초 (평균 {s['avg_elapsed']}초/사이클)")
    print(f"  총 기사: {s['total_articles']}건 | 총 요약: {s['total_summaries']}건 | 총 태그: {s['total_tags']}개")
    print(f"  리포트: {report_path}")

    return report
