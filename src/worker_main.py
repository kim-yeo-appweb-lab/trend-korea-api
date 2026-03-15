# ⚠️ DEPRECATED: Docker 환경에서는 supercronic + trend-korea-cron CLI를 사용합니다.
# 이 파일은 로컬 개발 전용으로 유지됩니다.
# 프로덕션 crontab 설정은 프로젝트 루트의 `crontab` 파일을 참조하세요.

from apscheduler.schedulers.blocking import BlockingScheduler

from src.core.config import get_settings
from src.core.logging import configure_logging
from src.db import Base
from src.db.session import engine
from src.scheduler.jobs import (
    cleanup_keyword_states,
    cleanup_refresh_tokens,
    collect_keywords,
    recalculate_community_hot_score,
    recalculate_search_rankings,
    reconcile_issue_status,
    run_job,
    run_news_collect_cycle,
)

settings = get_settings()


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone=settings.scheduler_timezone)

    scheduler.add_job(
        lambda: run_job("issue_status_reconcile", reconcile_issue_status),
        trigger="cron",
        minute="*/10",
        max_instances=1,
        coalesce=True,
        id="issue_status_reconcile",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_job("search_rankings", recalculate_search_rankings),
        trigger="cron",
        minute="*/10",
        max_instances=1,
        coalesce=True,
        id="search_rankings",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_job("community_hot_score", recalculate_community_hot_score),
        trigger="cron",
        minute="*/10",
        max_instances=1,
        coalesce=True,
        id="community_hot_score",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_job("cleanup_refresh_tokens", cleanup_refresh_tokens),
        trigger="cron",
        minute="*/10",
        max_instances=1,
        coalesce=True,
        id="cleanup_refresh_tokens",
        replace_existing=True,
    )

    # ── 키워드 수집 ──
    scheduler.add_job(
        lambda: run_job("keyword_collect", collect_keywords),
        trigger="cron",
        minute="*/10",
        max_instances=1,
        coalesce=True,
        id="keyword_collect",
        replace_existing=True,
    )

    # ── 뉴스 수집 파이프라인 ──
    scheduler.add_job(
        lambda: run_job("news_collect", run_news_collect_cycle),
        trigger="interval",
        minutes=settings.schedule_news_collect_minutes,
        max_instances=1,
        coalesce=True,
        id="news_collect",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_job("keyword_state_cleanup", cleanup_keyword_states),
        trigger="interval",
        minutes=settings.schedule_keyword_cleanup_minutes,
        max_instances=1,
        coalesce=True,
        id="keyword_state_cleanup",
        replace_existing=True,
    )

    return scheduler


def run() -> None:
    configure_logging()
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)

    scheduler = build_scheduler()
    scheduler.start()


if __name__ == "__main__":
    run()
