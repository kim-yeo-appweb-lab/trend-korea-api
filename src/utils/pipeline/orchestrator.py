"""키워드 수집 → 뉴스 크롤링 → 기사 분류 → 뉴스 요약 전체 파이프라인 오케스트레이터.

keyword_crawler와 news_summarizer는 직접 함수 호출,
news_crawler만 subprocess (외부 프로젝트).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.utils.keyword_crawler.crawler import CrawlOutput, run_crawl
from src.utils.naver_news_crawler.fetcher import run_fetch as naver_fetch, to_article_dicts
from src.utils.news_crawler.crawler import run_news_crawl
from src.utils.news_summarizer.summarizer import run_summarize

DEFAULT_REPEAT = 10
DEFAULT_TOP_N = 30
DEFAULT_MAX_KEYWORDS = 5
DEFAULT_LIMIT = 3


def _select_keywords(
    crawl_output: CrawlOutput,
    max_keywords: int,
    strategy: str,
) -> list[str]:
    """뉴스 크롤링에 사용할 키워드를 선별한다.

    strategy:
        "intersection" — 교집합 키워드 우선, 부족하면 aggregated에서 보충
        "aggregated"   — 기존 빈도 기반 상위 키워드만 사용
    """
    if strategy == "intersection" and crawl_output.intersection_keywords:
        selected = [kw.word for kw in crawl_output.intersection_keywords[:max_keywords]]
        if len(selected) < max_keywords:
            seen = set(selected)
            for kw in crawl_output.aggregated_keywords:
                if kw.word not in seen:
                    selected.append(kw.word)
                    seen.add(kw.word)
                if len(selected) >= max_keywords:
                    break
        return selected

    return [kw.word for kw in crawl_output.aggregated_keywords[:max_keywords]]


def _run_classification(
    articles: list[dict],
) -> tuple[list[dict], dict[str, int]]:
    """기사 분류/중복 제거를 실행하고 DUP 제외 기사와 통계를 반환한다."""
    from src.db.session import SessionLocal
    from src.utils.pipeline.feed_builder import persist_results
    from src.utils.pipeline.update_classifier import classify_batch

    db = SessionLocal()
    try:
        results = classify_batch(articles, db)
        stats = persist_results(results, db)
        db.commit()

        # DUP 제외 기사 article_id 목록
        from src.db.enums import UpdateType

        non_dup_ids = {
            r.article_id for r in results if r.update_type != UpdateType.DUP
        }

        # articles에서 DUP 기사 필터링 (원본 dict 반환)
        # article_id와 articles를 매핑하기 위해 URL 기반 필터링
        from src.utils.pipeline.update_classifier import normalize_url
        from sqlalchemy import select
        from src.db.raw_article import RawArticle

        non_dup_urls: set[str] = set()
        if non_dup_ids:
            stmt = select(RawArticle.canonical_url).where(
                RawArticle.id.in_(non_dup_ids)
            )
            rows = db.execute(stmt).scalars().all()
            non_dup_urls = set(rows)

        filtered = []
        for art in articles:
            url = art.get("url") or art.get("original_link") or art.get("link", "")
            if normalize_url(url) in non_dup_urls:
                filtered.append(art)

        return filtered, stats
    finally:
        db.close()


def run_cycle(
    cycle_num: int,
    cycle_dir: Path,
    top_n: int = DEFAULT_TOP_N,
    max_keywords: int = DEFAULT_MAX_KEYWORDS,
    limit: int = DEFAULT_LIMIT,
    model: str | None = None,
    *,
    use_naver: bool = True,
    keyword_strategy: str = "intersection",
    enable_classification: bool = True,
) -> dict:
    """한 사이클 실행. 결과 메타데이터 반환."""
    start = time.time()
    total_steps = 3 + int(use_naver) + int(enable_classification) * 2
    print(f"\n{'=' * 60}")
    print(f"  사이클 {cycle_num} 시작 ({datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC)")
    print(f"{'=' * 60}")

    cycle_dir.mkdir(parents=True, exist_ok=True)

    # 1. 키워드 수집 (직접 함수 호출)
    step = 1
    print(f"  [{step}/{total_steps}] 키워드 수집 중...")
    try:
        crawl_output = run_crawl(top_n_aggregated=top_n)
    except Exception as exc:
        print(f"  [키워드] 실패: {exc}")
        return {
            "cycle": cycle_num,
            "status": "fail",
            "stage": "keyword",
            "elapsed": time.time() - start,
        }

    if crawl_output.successful_channels == 0:
        return {
            "cycle": cycle_num,
            "status": "fail",
            "stage": "keyword",
            "elapsed": time.time() - start,
        }

    # 키워드 결과 저장
    kw_path = cycle_dir / "keywords.json"
    kw_data = crawl_output.to_dict()
    with kw_path.open("w", encoding="utf-8") as f:
        json.dump(kw_data, f, ensure_ascii=False, indent=2)

    agg_count = len(crawl_output.aggregated_keywords)
    if agg_count == 0:
        return {
            "cycle": cycle_num,
            "status": "fail",
            "stage": "keyword",
            "elapsed": time.time() - start,
        }

    # 교집합 키워드 정보
    ix_count = len(crawl_output.intersection_keywords)
    if ix_count > 0:
        ix_top = [kw.word for kw in crawl_output.intersection_keywords[:3]]
        print(
            f"  [키워드] {agg_count}개 추출, "
            f"교집합 {ix_count}개 ({crawl_output.min_channels}+ 채널), "
            f"상위: {ix_top}"
        )
    else:
        print(f"  [키워드] {agg_count}개 추출, 교집합 없음")

    # 전략에 따라 키워드 선별
    selected = _select_keywords(crawl_output, max_keywords, keyword_strategy)
    strategy_label = "교집합 우선" if keyword_strategy == "intersection" else "빈도순"
    print(f"  [키워드] {strategy_label} {len(selected)}개 선택: {selected}")

    # 2. 뉴스 크롤링 (subprocess — 외부 프로젝트)
    step += 1
    print(f"  [{step}/{total_steps}] 뉴스 크롤링 중...")
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
        articles = []

    # 3. 네이버 뉴스 검색 (선택)
    naver_count = 0
    if use_naver:
        step += 1
        print(f"  [{step}/{total_steps}] 네이버 뉴스 검색 중...")
        try:
            naver_result = naver_fetch(
                keywords=selected,
                display=limit,
                max_start=limit,
                sort="date",
            )
            naver_articles = to_article_dicts(naver_result, limit_per_keyword=limit)
            naver_count = len(naver_articles)
            articles.extend(naver_articles)
            print(f"  [네이버] {naver_count}건 수집 완료")
        except Exception as exc:
            print(f"  [네이버] 실패 (무시): {exc}")

    # 병합 결과 저장 (crawl.json 갱신)
    if articles:
        with crawl_path.open("w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

    article_count = len(articles)
    if article_count == 0:
        return {
            "cycle": cycle_num,
            "status": "fail",
            "stage": "crawl",
            "elapsed": time.time() - start,
        }

    # 4. 기사 분류/중복 제거 (신규)
    classify_stats: dict[str, int] = {}
    if enable_classification:
        step += 1
        print(f"  [{step}/{total_steps}] 기사 분류/중복 제거 중...")
        try:
            articles, classify_stats = _run_classification(articles)
            dup_count = classify_stats.get("dup", 0)
            print(
                f"  [분류] 완료: NEW={classify_stats.get('new', 0)}, "
                f"MINOR={classify_stats.get('minor', 0)}, "
                f"MAJOR={classify_stats.get('major', 0)}, "
                f"DUP={dup_count}"
            )
            if not articles:
                print("  [분류] 모든 기사가 중복 — 요약 건너뜀")
                return {
                    "cycle": cycle_num,
                    "status": "ok",
                    "elapsed": round(time.time() - start, 1),
                    "keywords_extracted": agg_count,
                    "keywords_used": len(selected),
                    "intersection_count": ix_count,
                    "articles_collected": article_count,
                    "naver_articles": naver_count,
                    "classification": classify_stats,
                    "summaries": 0,
                    "total_tags": 0,
                }
        except Exception as exc:
            print(f"  [분류] 실패 (무시, 전체 기사로 진행): {exc}")

        # 필터링된 기사로 crawl.json 갱신
        if articles:
            with crawl_path.open("w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)

    # 5. 뉴스 요약 (직접 함수 호출) — DUP 제외 기사만 요약
    step += 1
    print(f"  [{step}/{total_steps}] 뉴스 요약 중...")
    summary_path = cycle_dir / "summary.json"
    try:
        summary = run_summarize(str(crawl_path), str(summary_path), model)
    except Exception as exc:
        print(f"  [요약] 실패: {exc}")
        return {
            "cycle": cycle_num,
            "status": "fail",
            "stage": "summarize",
            "elapsed": time.time() - start,
        }

    elapsed = time.time() - start
    kw_summaries = summary.get("keywords", [])
    total_tags = sum(len(kw.get("tags", [])) for kw in kw_summaries)

    result = {
        "cycle": cycle_num,
        "status": "ok",
        "elapsed": round(elapsed, 1),
        "keywords_extracted": agg_count,
        "keywords_used": len(selected),
        "intersection_count": ix_count,
        "articles_collected": article_count,
        "naver_articles": naver_count,
        "summaries": len(kw_summaries),
        "total_tags": total_tags,
        "tokens": summary.get("total_tokens", {}),
        "model": summary.get("model", ""),
    }
    if classify_stats:
        result["classification"] = classify_stats

    print(
        f"  [완료] {elapsed:.1f}초 | 기사 {article_count}건 | 요약 {len(kw_summaries)}건 | 태그 {total_tags}개"
    )
    return result


def run_full_pipeline(
    repeat: int = DEFAULT_REPEAT,
    top_n: int = DEFAULT_TOP_N,
    max_keywords: int = DEFAULT_MAX_KEYWORDS,
    limit: int = DEFAULT_LIMIT,
    model: str | None = None,
    output_dir: Path | None = None,
    *,
    use_naver: bool = True,
    keyword_strategy: str = "intersection",
    enable_classification: bool = True,
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
    naver_label = "ON" if use_naver else "OFF"
    classify_label = "ON" if enable_classification else "OFF"
    print(
        f"  설정: top_n={top_n}, max_keywords={max_keywords}, limit={limit}, "
        f"model={model}, naver={naver_label}, strategy={keyword_strategy}, "
        f"classify={classify_label}"
    )

    all_results: list[dict] = []
    total_start = time.time()

    for i in range(1, repeat + 1):
        cycle_dir = run_dir / f"cycle_{i:02d}"
        result = run_cycle(
            i,
            cycle_dir,
            top_n,
            max_keywords,
            limit,
            model,
            use_naver=use_naver,
            keyword_strategy=keyword_strategy,
            enable_classification=enable_classification,
        )
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
            "keyword_strategy": keyword_strategy,
            "enable_classification": enable_classification,
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
    print(
        f"  총 기사: {s['total_articles']}건 | 총 요약: {s['total_summaries']}건 | 총 태그: {s['total_tags']}개"
    )
    print(f"  리포트: {report_path}")

    return report
