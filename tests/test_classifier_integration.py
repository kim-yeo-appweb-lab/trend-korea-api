"""분류기 통합 테스트 — DB 연동 테스트."""

from sqlalchemy.orm import Session

from src.db.enums import KeywordLinkStatus, UpdateType
from src.utils.pipeline.update_classifier import (
    check_exact_duplicate,
    check_near_duplicate,
    classify_article,
    find_candidate_issues,
)


class TestExactDuplicate:
    def test_no_duplicate(self, db_session: Session):
        result = check_exact_duplicate("https://unique-url.com/article", db_session)
        assert result is None

    def test_exact_duplicate_found(self, db_session: Session, create_raw_article):
        article = create_raw_article(
            title="중복 테스트",
            canonical_url="https://example.com/dup-test",
        )
        result = check_exact_duplicate("https://example.com/dup-test", db_session)
        assert result == article.id


class TestNearDuplicate:
    def test_no_near_duplicate(self, db_session: Session):
        result = check_near_duplicate("unique-hash-1", "unique-hash-2", db_session)
        assert result is None

    def test_title_hash_match(self, db_session: Session, create_raw_article):
        article = create_raw_article(
            title="해시 테스트",
            title_hash="matching-title-hash",
        )
        result = check_near_duplicate("matching-title-hash", "different-sem", db_session)
        assert result == article.id

    def test_semantic_hash_match(self, db_session: Session, create_raw_article):
        article = create_raw_article(
            title="시맨틱 테스트",
            semantic_hash="matching-semantic-hash",
        )
        result = check_near_duplicate("diff-title", "matching-semantic-hash", db_session)
        assert result == article.id


class TestFindCandidateIssues:
    def test_no_candidates(self, db_session: Session):
        result = find_candidate_issues(["없는키워드"], 72, db_session)
        assert result == []

    def test_empty_keywords(self, db_session: Session):
        result = find_candidate_issues([], 72, db_session)
        assert result == []

    def test_matches_active_keywords(
        self, db_session: Session, create_issue, create_issue_keyword_state
    ):
        issue = create_issue(title="매칭 테스트 이슈")
        create_issue_keyword_state(
            issue_id=issue.id,
            keyword="반도체",
            status=KeywordLinkStatus.ACTIVE,
        )
        result = find_candidate_issues(["반도체"], 72, db_session)
        assert len(result) == 1
        assert result[0][0] == issue.id
        assert result[0][1] == 1.0  # 1/1 키워드 매칭

    def test_partial_keyword_match(
        self, db_session: Session, create_issue, create_issue_keyword_state
    ):
        issue = create_issue(title="부분 매칭 이슈")
        create_issue_keyword_state(issue_id=issue.id, keyword="반도체")
        result = find_candidate_issues(["반도체", "경제"], 72, db_session)
        assert len(result) == 1
        assert result[0][1] == 0.5  # 1/2 키워드 매칭


class TestClassifyArticle:
    def test_new_article(self, db_session: Session):
        article = {
            "url": "https://brand-new-article.com/unique-123",
            "title": "완전히 새로운 기사 제목 유니크",
            "content": "본문 내용 유니크한 내용입니다",
            "keywords": ["존재하지않는키워드xyz"],
        }
        result = classify_article(article, db_session)
        assert result.update_type == UpdateType.NEW
        assert result.article_id is not None
        assert result.duplicate_of_id is None

    def test_exact_url_duplicate(self, db_session: Session, create_raw_article):
        existing = create_raw_article(
            title="기존 기사",
            canonical_url="https://example.com/existing-article",
        )
        article = {
            "url": "https://example.com/existing-article",
            "title": "같은 URL의 기사",
        }
        result = classify_article(article, db_session)
        assert result.update_type == UpdateType.DUP
        assert result.duplicate_of_id == existing.id

    def test_idempotent_insert(self, db_session: Session):
        """같은 기사를 두 번 분류하면 두 번째는 DUP."""
        article = {
            "url": "https://idempotent-test.com/article-999",
            "title": "멱등성 테스트 기사 제목",
            "content": "멱등성 테스트 본문",
        }
        result1 = classify_article(article, db_session)
        assert result1.update_type == UpdateType.NEW

        result2 = classify_article(article, db_session)
        assert result2.update_type == UpdateType.DUP
