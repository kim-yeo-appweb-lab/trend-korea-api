"""뉴스 수집 파이프라인 스케줄러 잡.

배치 주기:
- keyword_collect: 10분 — 트렌드 키워드 수집 → DB 저장
- news_collect: 10분 — 키워드 수집 → 뉴스 크롤링 → 분류/중복 제거 → 요약 → 피드 저장
- keyword_state_cleanup: 10분 — cooldown/closed 상태 전환
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.orm import Session

from src.db.enums import KeywordLinkStatus

logger = logging.getLogger(__name__)


def collect_keywords(db: Session) -> str | None:
    """트렌드 키워드를 수집하여 crawled_keywords / keyword_intersections에 저장한다."""
    from src.utils.keyword_crawler.crawler import run_crawl, save_to_db

    try:
        result = run_crawl(top_n_aggregated=30)
    except Exception:
        logger.exception("[keyword_collect] 크롤링 실패")
        raise

    if result.successful_channels == 0:
        detail = "channels=0, 수집 실패"
        logger.warning(f"[keyword_collect] {detail}")
        return detail

    saved = save_to_db(result)

    detail = (
        f"channels={result.successful_channels}/{result.total_channels}, "
        f"aggregated={len(result.aggregated_keywords)}, "
        f"intersection={len(result.intersection_keywords)}, "
        f"saved={saved}"
    )
    logger.info(f"[keyword_collect] {detail}")
    return detail


def run_news_collect_cycle(db: Session) -> str | None:
    """뉴스 수집 + 분류 + 요약 전체 사이클을 1회 실행한다.

    파이프라인은 내부에서 별도 세션을 사용하므로,
    이 함수의 db 파라미터는 잡 기록용으로만 사용된다.
    """
    from src.core.config import get_settings
    from src.utils.pipeline.orchestrator import run_cycle

    settings = get_settings()

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    output_dir = project_root / "cycle_outputs"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cycle_dir = output_dir / f"scheduled_{timestamp}"

    try:
        result = run_cycle(
            cycle_num=1,
            cycle_dir=cycle_dir,
            top_n=30,
            max_keywords=5,
            limit=3,
            model=None,
            use_naver=bool(settings.naver_api_client),
            keyword_strategy="intersection",
            enable_classification=True,
        )

        status = result.get("status", "unknown")
        articles = result.get("articles_collected", 0)
        summaries = result.get("summaries", 0)
        classification = result.get("classification", {})
        elapsed = result.get("elapsed", 0)

        # 결과 JSON 저장
        report_path = cycle_dir / "cycle_report.json"
        cycle_dir.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        detail = (
            f"status={status}, articles={articles}, summaries={summaries}, "
            f"new={classification.get('new', 0)}, minor={classification.get('minor', 0)}, "
            f"major={classification.get('major', 0)}, dup={classification.get('dup', 0)}, "
            f"elapsed={elapsed}s"
        )
        logger.info(f"[news_collect] {detail}")
        return detail

    except Exception:
        logger.exception("[news_collect] 사이클 실패")
        raise


def cleanup_keyword_states(db: Session) -> str | None:
    """이슈 키워드 상태를 정리한다.

    - last_seen_at이 48시간 경과한 ACTIVE → COOLDOWN
    - last_seen_at이 72시간 추가 경과한 COOLDOWN → CLOSED
    """
    from src.models.issues import IssueKeywordState

    now = datetime.now(timezone.utc)
    cooldown_cutoff = now - timedelta(hours=48)
    closed_cutoff = now - timedelta(hours=120)  # 48 + 72

    # ACTIVE → COOLDOWN
    cooldown_result = db.execute(
        update(IssueKeywordState)
        .where(
            IssueKeywordState.status == KeywordLinkStatus.ACTIVE,
            IssueKeywordState.last_seen_at < cooldown_cutoff,
        )
        .values(status=KeywordLinkStatus.COOLDOWN)
    )
    cooldown_count = cooldown_result.rowcount

    # COOLDOWN → CLOSED
    closed_result = db.execute(
        update(IssueKeywordState)
        .where(
            IssueKeywordState.status == KeywordLinkStatus.COOLDOWN,
            IssueKeywordState.last_seen_at < closed_cutoff,
        )
        .values(status=KeywordLinkStatus.CLOSED)
    )
    closed_count = closed_result.rowcount

    detail = f"cooldown={cooldown_count}, closed={closed_count}"
    logger.info(f"[keyword_state_cleanup] {detail}")
    return detail
