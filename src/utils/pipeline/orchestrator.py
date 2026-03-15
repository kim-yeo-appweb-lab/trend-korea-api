"""키워드 수집 → 메인페이지 헤드라인 ES 매칭 → 본문 수집 → 분류 → 요약 파이프라인.

keyword_crawler가 메인페이지를 스크래핑할 때 헤드라인 URL도 함께 추출하고,
ES nori 형태소 매칭으로 트렌드 키워드와 관련된 기사만 필터링한 뒤 본문을 수집한다.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from src.utils.keyword_crawler.crawler import CrawlOutput, run_crawl
from src.utils.keyword_crawler.headline_extractor import HeadlineItem
from src.utils.news_collector.content_fetcher import fetch_articles_content
from src.utils.news_summarizer.summarizer import run_summarize
from src.utils.pipeline.quality_gate import check_dup_ratio

logger = logging.getLogger(__name__)

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


# ── 헤드라인 → ES 매칭 ─────────────────────────────────────


def _headline_items_to_articles(items: list[HeadlineItem]) -> list[dict]:
    """HeadlineItem → ES 인덱싱/검색용 article dict 변환."""
    return [
        {
            "title": item.title,
            "url": item.url,
            "source_name": item.source_name,
            "channel_code": item.channel_code,
            "content_text": "",
        }
        for item in items
    ]


def _match_headlines_python(
    articles: list[dict],
    keywords: list[str],
    min_matches: int = 1,
) -> list[dict]:
    """Python 문자열 매칭 폴백: 제목에 키워드 포함 여부로 필터링."""
    from src.utils.pipeline.update_classifier import normalize_url

    # URL 기준 중복 제거
    url_map: dict[str, dict] = {}
    for art in articles:
        url = art.get("url", "")
        if not url:
            continue
        norm = normalize_url(url)
        if norm not in url_map:
            url_map[norm] = art

    result: list[dict] = []
    for art in url_map.values():
        title = art.get("title", "")
        matched = [kw for kw in keywords if kw in title]
        if len(matched) >= min_matches:
            result.append({
                **art,
                "keyword": ", ".join(matched),
                "matched_keywords": matched,
                "keyword_count": len(matched),
                "confidence": min(0.6 + len(matched) * 0.1, 1.0),
            })

    result.sort(key=lambda a: (-a["keyword_count"], -a.get("confidence", 0)))
    return result


def _match_headlines_with_es(
    headline_items: list[HeadlineItem],
    keywords: list[str],
    min_matches: int = 1,
) -> list[dict]:
    """ES 매칭: 인덱싱 → 검색. 폴백: Python title 문자열 매칭."""
    articles = _headline_items_to_articles(headline_items)

    try:
        from src.utils.elasticsearch.client import is_es_available
        from src.utils.elasticsearch.indexer import bulk_index_articles
        from src.utils.elasticsearch.searcher import cross_reference_search
    except ImportError:
        print("  [ES] elasticsearch 미설치 — Python 문자열 매칭 폴백")
        return _match_headlines_python(articles, keywords, min_matches)

    if not is_es_available():
        print("  [ES] 연결 불가 — Python 문자열 매칭 폴백")
        return _match_headlines_python(articles, keywords, min_matches)

    indexed = bulk_index_articles(articles)
    print(f"  [ES] {indexed}/{len(articles)}건 인덱싱 완료")

    es_results = cross_reference_search(keywords, min_matches=min_matches)
    if not es_results:
        print("  [ES] 검색 결과 0건 — Python 문자열 매칭 폴백")
        return _match_headlines_python(articles, keywords, min_matches)

    print(f"  [ES] nori 형태소 매칭: {len(es_results)}건")
    return es_results


# ── 분류/중복 제거 ──────────────────────────────────────────


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

        non_dup_ids = {r.article_id for r in results if r.update_type != UpdateType.DUP}

        # articles에서 DUP 기사 필터링 (URL 기반)
        from sqlalchemy import select

        from src.models.pipeline import RawArticle
        from src.utils.pipeline.update_classifier import normalize_url

        non_dup_urls: set[str] = set()
        if non_dup_ids:
            stmt = select(RawArticle.canonical_url).where(RawArticle.id.in_(non_dup_ids))
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


# ── 사이클 실행 ─────────────────────────────────────────────


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
    save_db: bool = True,
) -> dict:
    """한 사이클 실행: 키워드 수집 → ES 매칭 → 본문 수집 → 분류 → 요약."""
    start = time.time()
    total_steps = 4 + int(enable_classification and save_db)
    print(f"\n{'=' * 60}")
    print(f"  사이클 {cycle_num} 시작 ({datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC)")
    print(f"{'=' * 60}")

    cycle_dir.mkdir(parents=True, exist_ok=True)
    crawl_path = cycle_dir / "crawl.json"

    # ── 1. 키워드 수집 + 메인페이지 헤드라인 URL 추출 ──
    step = 1
    print(f"  [{step}/{total_steps}] 키워드 수집 + 헤드라인 추출 중...")
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
    headline_count = len(crawl_output.all_headline_items)
    if ix_count > 0:
        ix_top = [kw.word for kw in crawl_output.intersection_keywords[:3]]
        print(
            f"  [키워드] {agg_count}개 추출, "
            f"교집합 {ix_count}개 ({crawl_output.min_channels}+ 채널), "
            f"상위: {ix_top}"
        )
    else:
        print(f"  [키워드] {agg_count}개 추출, 교집합 없음")
    print(f"  [헤드라인] {headline_count}건 URL 추출 완료")

    # DB 저장: 키워드
    if save_db:
        from src.utils.keyword_crawler.crawler import save_to_db as save_keywords

        kw_saved = save_keywords(crawl_output)
        print(f"  [키워드] DB 저장: {kw_saved}건")

    # 전략에 따라 키워드 선별
    selected = _select_keywords(crawl_output, max_keywords, keyword_strategy)
    strategy_label = "교집합 우선" if keyword_strategy == "intersection" else "빈도순"
    print(f"  [키워드] {strategy_label} {len(selected)}개 선택: {selected}")

    # ── 2. 메인페이지 헤드라인 → ES 키워드 매칭 ──
    step += 1
    print(f"  [{step}/{total_steps}] ES 키워드 매칭 중...")
    headline_items = crawl_output.all_headline_items
    if not headline_items:
        print("  [매칭] 헤드라인 없음")
        return {
            "cycle": cycle_num,
            "status": "fail",
            "stage": "matching",
            "elapsed": time.time() - start,
        }

    matched_articles = _match_headlines_with_es(headline_items, selected)
    if not matched_articles:
        print("  [매칭] 매칭 기사 없음")
        return {
            "cycle": cycle_num,
            "status": "fail",
            "stage": "matching",
            "elapsed": time.time() - start,
            "headline_items": headline_count,
        }

    kw_counts: dict[int, int] = {}
    for a in matched_articles:
        kc = a.get("keyword_count", 1)
        kw_counts[kc] = kw_counts.get(kc, 0) + 1
    count_str = ", ".join(f"{k}개={v}건" for k, v in sorted(kw_counts.items(), reverse=True))
    print(f"  [매칭] {headline_count}건 → {len(matched_articles)}건 ({count_str})")

    # ── 3. 매칭 기사만 본문 수집 ──
    step += 1
    print(f"  [{step}/{total_steps}] 매칭 기사 본문 수집 중 ({len(matched_articles)}건)...")
    try:
        articles = fetch_articles_content(matched_articles)
    except Exception as exc:
        print(f"  [본문] 수집 실패: {exc}")
        articles = matched_articles  # 본문 없이 제목만으로 진행

    content_count = sum(1 for a in articles if a.get("content_text"))
    print(f"  [본문] {content_count}/{len(articles)}건 본문 수집 완료")

    # 결과 저장
    with crawl_path.open("w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    raw_article_count = len(articles)
    article_count = raw_article_count

    # ── 4. 기사 분류/중복 제거 ──
    classify_stats: dict[str, int] = {}
    if enable_classification and save_db:
        step += 1
        print(f"  [{step}/{total_steps}] 기사 분류/중복 제거 중...")
        try:
            articles, classify_stats = _run_classification(articles)
            print(
                f"  [분류] 완료: NEW={classify_stats.get('new', 0)}, "
                f"MINOR={classify_stats.get('minor', 0)}, "
                f"MAJOR={classify_stats.get('major', 0)}, "
                f"DUP={classify_stats.get('dup', 0)}"
            )
            # 품질 게이트: DUP 비율 검사
            if check_dup_ratio(classify_stats):
                print("  [품질 게이트] DUP 비율 80% 초과 — 요약 건너뜀")
                return {
                    "cycle": cycle_num,
                    "status": "ok",
                    "elapsed": round(time.time() - start, 1),
                    "keywords_extracted": agg_count,
                    "keywords_used": len(selected),
                    "intersection_count": ix_count,
                    "headline_items": headline_count,
                    "matched_articles": len(matched_articles),
                    "articles_collected": article_count,
                    "classification": classify_stats,
                    "summaries": 0,
                    "total_tags": 0,
                    "early_stop": "dup_ratio",
                }

            if not articles:
                print("  [분류] 모든 기사가 중복 — 요약 건너뜀")
                return {
                    "cycle": cycle_num,
                    "status": "ok",
                    "elapsed": round(time.time() - start, 1),
                    "keywords_extracted": agg_count,
                    "keywords_used": len(selected),
                    "intersection_count": ix_count,
                    "headline_items": headline_count,
                    "matched_articles": len(matched_articles),
                    "articles_collected": article_count,
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

    # ── 5. 뉴스 요약 ──
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
            "headline_items": headline_count,
            "matched_articles": len(matched_articles),
            "articles_collected": article_count,
        }

    # DB 저장: 뉴스 요약
    if save_db:
        try:
            from src.utils.news_summarizer.summarizer import save_to_db as save_summary

            batch_id = save_summary(summary)
            print(f"  [요약] DB 저장: batch_id={batch_id}")
        except Exception as exc:
            print(f"  [요약] DB 저장 실패 (무시): {exc}")

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
        "headline_items": headline_count,
        "matched_articles": len(matched_articles),
        "articles_collected": article_count,
        "summaries": len(kw_summaries),
        "total_tags": total_tags,
        "tokens": summary.get("total_tokens", {}),
        "model": summary.get("model", ""),
    }
    if classify_stats:
        result["classification"] = classify_stats

    print(
        f"  [완료] {elapsed:.1f}초 | 헤드라인 {headline_count}건"
        f" → 매칭 {len(matched_articles)}건 → 기사 {article_count}건"
        f" | 요약 {len(kw_summaries)}건 | 태그 {total_tags}개"
    )
    return result


# ── 반복 실행 ────────────────────────────────────────────────


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
    save_db: bool = True,
) -> dict:
    """전체 파이프라인을 반복 실행한다."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if output_dir is None:
        output_dir = project_root / "cycle_outputs"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    classify_label = "ON" if enable_classification else "OFF"
    print(f"전체 파이프라인 반복 실행 ({repeat}회)")
    print(f"  출력 디렉토리: {run_dir}")
    print(
        f"  설정: top_n={top_n}, max_keywords={max_keywords}, "
        f"model={model}, strategy={keyword_strategy}, "
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
            save_db=save_db,
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
        f"  총 기사: {s['total_articles']}건 | 총 요약: {s['total_summaries']}건"
        f" | 총 태그: {s['total_tags']}개"
    )
    print(f"  리포트: {report_path}")

    return report
