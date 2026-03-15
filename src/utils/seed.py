"""개발용 더미 데이터 시드 스크립트.

사용법:
    uv run trend-korea-seed          # 시드 데이터 삽입
    uv run trend-korea-seed --reset   # 기존 데이터 삭제 후 재삽입
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text

from src.core.security import hash_password
from src.db.enums import (
    Importance,
    IssueStatus,
    SourceEntityType,
    TagType,
    TriggerType,
    UserRole,
    VerificationStatus,
)
from src.db.session import engine

# 고정 ID (FK 참조용)
ADMIN_ID = "00000000-0000-0000-0000-000000000001"
MEMBER_1_ID = "00000000-0000-0000-0000-000000000002"
MEMBER_2_ID = "00000000-0000-0000-0000-000000000003"

TAG_IDS = {
    "politics": "10000000-0000-0000-0000-000000000001",
    "economy": "10000000-0000-0000-0000-000000000002",
    "society": "10000000-0000-0000-0000-000000000003",
    "tech": "10000000-0000-0000-0000-000000000004",
    "seoul": "10000000-0000-0000-0000-000000000005",
    "busan": "10000000-0000-0000-0000-000000000006",
}

EVENT_IDS = [f"20000000-0000-0000-0000-00000000000{i}" for i in range(1, 6)]
ISSUE_IDS = [f"30000000-0000-0000-0000-00000000000{i}" for i in range(1, 4)]
TRIGGER_IDS = [f"40000000-0000-0000-0000-00000000000{i}" for i in range(1, 5)]
SOURCE_IDS = [f"50000000-0000-0000-0000-00000000000{i}" for i in range(1, 7)]
POST_IDS = [f"60000000-0000-0000-0000-00000000000{i}" for i in range(1, 4)]
COMMENT_IDS = [f"70000000-0000-0000-0000-00000000000{i}" for i in range(1, 4)]

now = datetime.now(timezone.utc)
password = hash_password("password123!")


def _ts(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    return now - timedelta(days=days_ago, hours=hours_ago)


def seed_users(conn):
    conn.execute(text("""
        INSERT INTO users (id, nickname, email, password_hash, role, is_active, created_at, updated_at)
        VALUES
            (:admin_id, '관리자', 'admin@test.com', :pw, :admin_role, true, :ts, :ts),
            (:m1_id, '테스트유저1', 'user1@test.com', :pw, :member_role, true, :ts, :ts),
            (:m2_id, '테스트유저2', 'user2@test.com', :pw, :member_role, true, :ts, :ts)
        ON CONFLICT (id) DO NOTHING
    """), {
        "admin_id": ADMIN_ID, "m1_id": MEMBER_1_ID, "m2_id": MEMBER_2_ID,
        "pw": password, "admin_role": UserRole.ADMIN.value,
        "member_role": UserRole.MEMBER.value, "ts": _ts(30),
    })


def seed_tags(conn):
    tags = [
        (TAG_IDS["politics"], "정치", TagType.CATEGORY.value, "politics"),
        (TAG_IDS["economy"], "경제", TagType.CATEGORY.value, "economy"),
        (TAG_IDS["society"], "사회", TagType.CATEGORY.value, "society"),
        (TAG_IDS["tech"], "기술", TagType.CATEGORY.value, "tech"),
        (TAG_IDS["seoul"], "서울", TagType.REGION.value, "seoul"),
        (TAG_IDS["busan"], "부산", TagType.REGION.value, "busan"),
    ]
    for tag_id, name, tag_type, slug in tags:
        conn.execute(text("""
            INSERT INTO tags (id, name, type, slug, updated_at)
            VALUES (:id, :name, :type, :slug, :ts)
            ON CONFLICT (id) DO NOTHING
        """), {"id": tag_id, "name": name, "type": tag_type, "slug": slug, "ts": now})


def seed_events(conn):
    events = [
        (EVENT_IDS[0], "반도체 수출 역대 최고 실적", "2026년 1분기 반도체 수출이 역대 최고치를 기록했다.",
         Importance.HIGH, VerificationStatus.VERIFIED, 2, 5),
        (EVENT_IDS[1], "수도권 폭우 피해 발생", "수도권 일대에 시간당 80mm 이상의 폭우가 내려 피해가 발생했다.",
         Importance.HIGH, VerificationStatus.VERIFIED, 3, 3),
        (EVENT_IDS[2], "신규 AI 규제법안 발의", "국회에서 인공지능 관련 규제 법안이 발의되었다.",
         Importance.MEDIUM, VerificationStatus.UNVERIFIED, 1, 7),
        (EVENT_IDS[3], "부산 신항 물류 허브 착공", "부산 신항 배후 물류 허브 착공식이 진행되었다.",
         Importance.MEDIUM, VerificationStatus.VERIFIED, 1, 10),
        (EVENT_IDS[4], "전국 교통 대란 예고", "철도 노조 파업으로 전국 교통 대란이 예고되었다.",
         Importance.LOW, VerificationStatus.UNVERIFIED, 0, 1),
    ]
    for eid, title, summary, importance, vs, src_cnt, days in events:
        conn.execute(text("""
            INSERT INTO events (id, occurred_at, title, summary, importance,
                                verification_status, source_count, created_at, updated_at)
            VALUES (:id, :occurred_at, :title, :summary, :importance,
                    :vs, :src_cnt, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": eid, "occurred_at": _ts(days), "title": title, "summary": summary,
            "importance": importance.value, "vs": vs.value,
            "src_cnt": src_cnt, "created_at": _ts(days), "updated_at": _ts(days),
        })

    # event-tag 연결
    event_tag_pairs = [
        (EVENT_IDS[0], TAG_IDS["economy"]),
        (EVENT_IDS[0], TAG_IDS["tech"]),
        (EVENT_IDS[1], TAG_IDS["society"]),
        (EVENT_IDS[1], TAG_IDS["seoul"]),
        (EVENT_IDS[2], TAG_IDS["politics"]),
        (EVENT_IDS[2], TAG_IDS["tech"]),
        (EVENT_IDS[3], TAG_IDS["economy"]),
        (EVENT_IDS[3], TAG_IDS["busan"]),
        (EVENT_IDS[4], TAG_IDS["society"]),
    ]
    for event_id, tag_id in event_tag_pairs:
        conn.execute(text("""
            INSERT INTO event_tags (event_id, tag_id)
            VALUES (:eid, :tid)
            ON CONFLICT DO NOTHING
        """), {"eid": event_id, "tid": tag_id})


def seed_issues(conn):
    issues = [
        (ISSUE_IDS[0], "반도체 산업 동향", "글로벌 반도체 공급망 변화와 한국 반도체 산업의 대응을 추적합니다.",
         IssueStatus.ONGOING, 15, 2),
        (ISSUE_IDS[1], "AI 규제 논의", "인공지능 기술 규제에 대한 국내외 동향을 추적합니다.",
         IssueStatus.ONGOING, 8, 5),
        (ISSUE_IDS[2], "기후 변화 대응", "기후 변화에 대한 정부 대응 정책을 추적합니다.",
         IssueStatus.CLOSED, 3, 15),
    ]
    for iid, title, desc, status, tracker, days in issues:
        conn.execute(text("""
            INSERT INTO issues (id, title, description, status, tracker_count,
                               latest_trigger_at, created_at, updated_at)
            VALUES (:id, :title, :desc, :status, :tracker,
                    :trigger_at, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": iid, "title": title, "desc": desc,
            "status": status.value, "tracker": tracker,
            "trigger_at": _ts(days - 1), "created_at": _ts(days), "updated_at": _ts(1),
        })

    # issue-event 연결
    conn.execute(text("""
        INSERT INTO issue_events (issue_id, event_id) VALUES (:iid, :eid)
        ON CONFLICT DO NOTHING
    """), {"iid": ISSUE_IDS[0], "eid": EVENT_IDS[0]})
    conn.execute(text("""
        INSERT INTO issue_events (issue_id, event_id) VALUES (:iid, :eid)
        ON CONFLICT DO NOTHING
    """), {"iid": ISSUE_IDS[1], "eid": EVENT_IDS[2]})

    # issue-tag 연결
    issue_tag_pairs = [
        (ISSUE_IDS[0], TAG_IDS["economy"]),
        (ISSUE_IDS[0], TAG_IDS["tech"]),
        (ISSUE_IDS[1], TAG_IDS["politics"]),
        (ISSUE_IDS[1], TAG_IDS["tech"]),
        (ISSUE_IDS[2], TAG_IDS["society"]),
    ]
    for issue_id, tag_id in issue_tag_pairs:
        conn.execute(text("""
            INSERT INTO issue_tags (issue_id, tag_id) VALUES (:iid, :tid)
            ON CONFLICT DO NOTHING
        """), {"iid": issue_id, "tid": tag_id})


def seed_triggers(conn):
    triggers = [
        (TRIGGER_IDS[0], ISSUE_IDS[0], "삼성전자, HBM4 양산 계획 발표",
         TriggerType.ANNOUNCEMENT, 2),
        (TRIGGER_IDS[1], ISSUE_IDS[0], "SK하이닉스 분기 실적 공개",
         TriggerType.ARTICLE, 1),
        (TRIGGER_IDS[2], ISSUE_IDS[1], "국회 AI 특위 1차 회의 개최",
         TriggerType.ARTICLE, 5),
        (TRIGGER_IDS[3], ISSUE_IDS[1], "EU AI Act 시행 후 국내 영향 분석 보고서",
         TriggerType.ARTICLE, 3),
    ]
    for tid, issue_id, summary, ttype, days in triggers:
        conn.execute(text("""
            INSERT INTO triggers (id, issue_id, occurred_at, summary, type, created_at, updated_at)
            VALUES (:id, :issue_id, :occurred_at, :summary, :type, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": tid, "issue_id": issue_id, "occurred_at": _ts(days),
            "summary": summary, "type": ttype.value,
            "created_at": _ts(days), "updated_at": _ts(days),
        })


def seed_sources(conn):
    sources = [
        (SOURCE_IDS[0], SourceEntityType.EVENT, EVENT_IDS[0],
         "https://example.com/news/1", "반도체 수출 역대 최고", "연합뉴스", 5),
        (SOURCE_IDS[1], SourceEntityType.EVENT, EVENT_IDS[0],
         "https://example.com/news/2", "반도체 호황, 경제 성장 견인", "한국경제", 4),
        (SOURCE_IDS[2], SourceEntityType.EVENT, EVENT_IDS[1],
         "https://example.com/news/3", "수도권 폭우 피해 속출", "KBS뉴스", 3),
        (SOURCE_IDS[3], SourceEntityType.ISSUE, ISSUE_IDS[0],
         "https://example.com/news/4", "반도체 산업 전망 보고서", "전자신문", 7),
        (SOURCE_IDS[4], SourceEntityType.TRIGGER, TRIGGER_IDS[0],
         "https://example.com/news/5", "삼성 HBM4 양산 시기 확정", "조선일보", 2),
        (SOURCE_IDS[5], SourceEntityType.TRIGGER, TRIGGER_IDS[2],
         "https://example.com/news/6", "국회 AI 규제 첫 논의", "MBC뉴스", 5),
    ]
    for sid, entity_type, entity_id, url, title, publisher, days in sources:
        conn.execute(text("""
            INSERT INTO sources (id, entity_type, entity_id, url, title, publisher, published_at)
            VALUES (:id, :entity_type, :entity_id, :url, :title, :publisher, :published_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": sid, "entity_type": entity_type.value, "entity_id": entity_id,
            "url": url, "title": title, "publisher": publisher, "published_at": _ts(days),
        })


def seed_community(conn):
    posts = [
        (POST_IDS[0], MEMBER_1_ID, "반도체 수출 호조, 어떻게 생각하시나요?",
         "최근 반도체 수출이 역대 최고를 기록했는데 지속될 수 있을까요?", False, 3, 0, 2, 3),
        (POST_IDS[1], MEMBER_2_ID, "AI 규제, 찬성 vs 반대",
         "AI 규제법안에 대한 여러분의 생각은?", False, 5, 1, 1, 5),
        (POST_IDS[2], MEMBER_1_ID, "익명 고민 글",
         "요즘 취업 준비하는데 AI 시대에 어떤 직종이 유망할까요?", True, 1, 0, 0, 2),
    ]
    for pid, author_id, title, content, is_anon, likes, dislikes, comments, days in posts:
        conn.execute(text("""
            INSERT INTO posts (id, author_id, title, content, is_anonymous,
                              like_count, dislike_count, comment_count, created_at, updated_at)
            VALUES (:id, :author_id, :title, :content, :is_anon,
                    :likes, :dislikes, :comments, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": pid, "author_id": author_id, "title": title, "content": content,
            "is_anon": is_anon, "likes": likes, "dislikes": dislikes, "comments": comments,
            "created_at": _ts(days), "updated_at": _ts(days),
        })

    comments = [
        (COMMENT_IDS[0], POST_IDS[0], None, MEMBER_2_ID,
         "장기적으로 좋은 신호라고 봅니다.", 1, 3),
        (COMMENT_IDS[1], POST_IDS[0], COMMENT_IDS[0], MEMBER_1_ID,
         "동의합니다. 하지만 미중 갈등이 변수네요.", 0, 2),
        (COMMENT_IDS[2], POST_IDS[1], None, MEMBER_1_ID,
         "적절한 규제는 필요하다고 생각합니다.", 2, 4),
    ]
    for cid, post_id, parent_id, author_id, content, likes, days in comments:
        conn.execute(text("""
            INSERT INTO comments (id, post_id, parent_id, author_id, content,
                                 like_count, created_at, updated_at)
            VALUES (:id, :post_id, :parent_id, :author_id, :content,
                    :likes, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": cid, "post_id": post_id, "parent_id": parent_id,
            "author_id": author_id, "content": content,
            "likes": likes, "created_at": _ts(days), "updated_at": _ts(days),
        })


def reset_data(conn):
    """시드 데이터 관련 테이블을 역순으로 비운다."""
    tables = [
        "comment_likes", "post_votes", "comments", "posts", "post_tags",
        "sources", "triggers",
        "issue_keyword_states", "issue_keyword_aliases", "issue_rank_snapshots",
        "issue_events", "issue_tags", "user_tracked_issues", "issues",
        "event_tags", "user_saved_events", "events",
        "tags", "user_social_accounts", "users",
    ]
    for table in tables:
        conn.execute(text(f"DELETE FROM {table}"))


def run_seed(*, reset: bool = False):
    with engine.begin() as conn:
        if reset:
            print("기존 데이터 삭제 중...")
            reset_data(conn)

        print("시드 데이터 삽입 중...")
        seed_users(conn)
        seed_tags(conn)
        seed_events(conn)
        seed_issues(conn)
        seed_triggers(conn)
        seed_sources(conn)
        seed_community(conn)
        print("시드 데이터 삽입 완료!")
        print()
        print("테스트 계정:")
        print(f"  관리자  — admin@test.com / password123!")
        print(f"  유저1   — user1@test.com / password123!")
        print(f"  유저2   — user2@test.com / password123!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="개발용 더미 데이터 시드")
    parser.add_argument("--reset", action="store_true", help="기존 데이터 삭제 후 재삽입")
    args = parser.parse_args()
    run_seed(reset=args.reset)


if __name__ == "__main__":
    main()
