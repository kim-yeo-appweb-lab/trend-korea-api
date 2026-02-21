from apscheduler.schedulers.blocking import BlockingScheduler

from src.core.config import get_settings
from src.core.logging import configure_logging
from src.db import Base
from src.db.session import engine
from src.scheduler.jobs import (
    cleanup_refresh_tokens,
    recalculate_community_hot_score,
    recalculate_search_rankings,
    reconcile_issue_status,
    run_job,
)

settings = get_settings()


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone=settings.scheduler_timezone)

    scheduler.add_job(
        lambda: run_job("issue_status_reconcile", reconcile_issue_status),
        trigger="cron",
        minute="*/30",
        max_instances=1,
        coalesce=True,
        id="issue_status_reconcile",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_job("search_rankings", recalculate_search_rankings),
        trigger="cron",
        minute="0",
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
        hour="3",
        minute="0",
        max_instances=1,
        coalesce=True,
        id="cleanup_refresh_tokens",
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
