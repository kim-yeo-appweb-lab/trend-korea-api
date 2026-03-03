"""스케줄러 파이프라인 잡 테스트."""

from datetime import datetime, timedelta, timezone

from src.db.enums import KeywordLinkStatus
from src.scheduler.jobs.pipeline_jobs import cleanup_keyword_states


class TestCleanupKeywordStates:
    """키워드 상태 정리 잡 테스트."""

    def test_active_to_cooldown(self, db_session, create_issue, create_issue_keyword_state):
        """48시간 경과한 ACTIVE → COOLDOWN."""
        issue = create_issue(title="테스트 이슈")
        old_time = datetime.now(timezone.utc) - timedelta(hours=49)
        state = create_issue_keyword_state(
            issue_id=issue.id,
            keyword="테스트",
            status=KeywordLinkStatus.ACTIVE,
        )
        state.last_seen_at = old_time
        db_session.flush()

        result = cleanup_keyword_states(db_session)
        db_session.flush()

        db_session.refresh(state)
        assert state.status == KeywordLinkStatus.COOLDOWN
        assert "cooldown=1" in result

    def test_cooldown_to_closed(self, db_session, create_issue, create_issue_keyword_state):
        """120시간(48+72) 경과한 COOLDOWN → CLOSED."""
        issue = create_issue(title="테스트 이슈")
        old_time = datetime.now(timezone.utc) - timedelta(hours=121)
        state = create_issue_keyword_state(
            issue_id=issue.id,
            keyword="테스트",
            status=KeywordLinkStatus.COOLDOWN,
        )
        state.last_seen_at = old_time
        db_session.flush()

        result = cleanup_keyword_states(db_session)
        db_session.flush()

        db_session.refresh(state)
        assert state.status == KeywordLinkStatus.CLOSED
        assert "closed=1" in result

    def test_recent_active_unchanged(self, db_session, create_issue, create_issue_keyword_state):
        """최근 ACTIVE는 변경되지 않는다."""
        issue = create_issue(title="테스트 이슈")
        state = create_issue_keyword_state(
            issue_id=issue.id,
            keyword="테스트",
            status=KeywordLinkStatus.ACTIVE,
        )
        # last_seen_at은 기본값이 현재 시간

        result = cleanup_keyword_states(db_session)
        db_session.flush()

        db_session.refresh(state)
        assert state.status == KeywordLinkStatus.ACTIVE
        assert "cooldown=0" in result

    def test_recent_cooldown_unchanged(self, db_session, create_issue, create_issue_keyword_state):
        """48시간 이내 COOLDOWN은 CLOSED로 바뀌지 않는다."""
        issue = create_issue(title="테스트 이슈")
        recent_time = datetime.now(timezone.utc) - timedelta(hours=50)
        state = create_issue_keyword_state(
            issue_id=issue.id,
            keyword="테스트",
            status=KeywordLinkStatus.COOLDOWN,
        )
        state.last_seen_at = recent_time
        db_session.flush()

        result = cleanup_keyword_states(db_session)
        db_session.flush()

        db_session.refresh(state)
        assert state.status == KeywordLinkStatus.COOLDOWN
        assert "closed=0" in result

    def test_mixed_states(self, db_session, create_issue, create_issue_keyword_state):
        """여러 상태의 키워드를 동시에 처리한다."""
        issue = create_issue(title="테스트 이슈")

        # ACTIVE → COOLDOWN 대상
        s1 = create_issue_keyword_state(
            issue_id=issue.id, keyword="키워드1", status=KeywordLinkStatus.ACTIVE
        )
        s1.last_seen_at = datetime.now(timezone.utc) - timedelta(hours=49)

        # COOLDOWN → CLOSED 대상
        s2 = create_issue_keyword_state(
            issue_id=issue.id, keyword="키워드2", status=KeywordLinkStatus.COOLDOWN
        )
        s2.last_seen_at = datetime.now(timezone.utc) - timedelta(hours=121)

        # 유지
        s3 = create_issue_keyword_state(
            issue_id=issue.id, keyword="키워드3", status=KeywordLinkStatus.ACTIVE
        )
        db_session.flush()

        result = cleanup_keyword_states(db_session)
        db_session.flush()

        db_session.refresh(s1)
        db_session.refresh(s2)
        db_session.refresh(s3)
        assert s1.status == KeywordLinkStatus.COOLDOWN
        assert s2.status == KeywordLinkStatus.CLOSED
        assert s3.status == KeywordLinkStatus.ACTIVE


class TestWorkerMainImport:
    """worker_main에 잡이 올바르게 등록되었는지 확인."""

    def test_build_scheduler_has_pipeline_jobs(self):
        """build_scheduler에 news_collect과 keyword_state_cleanup 잡이 등록된다."""
        from src.worker_main import build_scheduler

        scheduler = build_scheduler()
        job_ids = [job.id for job in scheduler.get_jobs()]
        assert "news_collect" in job_ids
        assert "keyword_state_cleanup" in job_ids
