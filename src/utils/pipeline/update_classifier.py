"""뉴스 기사 분류 모듈.

수집된 기사를 NEW / MINOR_UPDATE / MAJOR_UPDATE / DUP 로 자동 분류한다.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.enums import KeywordLinkStatus, UpdateType
from src.db.event_update import EventUpdate
from src.db.issue_keyword_state import IssueKeywordState
from src.db.raw_article import RawArticle


@dataclass
class ClassificationResult:
    """기사 분류 결과."""

    article_id: str
    update_type: UpdateType
    matched_issue_id: str | None = None
    update_score: float = 0.0
    major_reasons: list[str] = field(default_factory=list)
    diff_summary: str = ""
    duplicate_of_id: str | None = None


# ── URL 정규화 ──


_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "source", "from",
})


def normalize_url(url: str) -> str:
    """URL을 정규화하여 추적 파라미터를 제거하고 소문자화한다."""
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower().rstrip(".")
    # www. 접두사 제거
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or "/"
    # 추적 파라미터 제거
    qs = parse_qs(parsed.query, keep_blank_values=False)
    filtered = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
    query = urlencode(filtered, doseq=True) if filtered else ""
    return urlunparse((scheme, netloc, path, "", query, ""))


# ── 해시 계산 ──


_WHITESPACE_RE = re.compile(r"\s+")
_PUNCTUATION_RE = re.compile(r"[^\w\s]", re.UNICODE)


def _normalize_text(text: str) -> str:
    """텍스트를 정규화: 소문자 + 공백 정리 + 특수문자 제거."""
    text = text.lower().strip()
    text = _PUNCTUATION_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def compute_title_hash(title: str) -> str:
    """제목의 SHA-256 해시를 계산한다."""
    normalized = _normalize_text(title)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_semantic_hash(title: str, content: str | None) -> str:
    """제목 + 본문 앞 200자를 결합한 시맨틱 해시."""
    normalized_title = _normalize_text(title)
    content_prefix = ""
    if content:
        content_prefix = _normalize_text(content[:200])
    combined = f"{normalized_title}|{content_prefix}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# ── 키워드 정규화 ──


def normalize_keywords(keywords: list[str] | None) -> list[str]:
    """키워드 목록을 정규화: 소문자 + 공백 정리 + 중복 제거."""
    if not keywords:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for kw in keywords:
        normalized = _normalize_text(kw)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


# ── 기사 정규화 ──


def normalize_article(article: dict) -> dict:
    """기사 딕셔너리를 정규화한다 (해시, URL, 키워드 포함)."""
    url = article.get("url") or article.get("original_link") or article.get("link", "")
    title = article.get("title", "")
    content = article.get("content") or article.get("description") or article.get("content_text")
    keywords = article.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    # 키워드가 없으면 기사에 keyword 필드가 있을 수 있음 (네이버 뉴스)
    if not keywords and article.get("keyword"):
        keywords = [article["keyword"]]

    return {
        **article,
        "canonical_url": normalize_url(url),
        "original_url": url,
        "title": title,
        "content_text": content,
        "source_name": article.get("source") or article.get("publisher", ""),
        "title_hash": compute_title_hash(title),
        "semantic_hash": compute_semantic_hash(title, content),
        "normalized_keywords": normalize_keywords(keywords),
        "entity_json": article.get("entities"),
        "published_at": article.get("published_at") or article.get("pub_date"),
    }


# ── 중복 검사 ──


def check_exact_duplicate(canonical_url: str, db: Session) -> str | None:
    """canonical_url이 이미 존재하면 기존 기사 ID 반환."""
    stmt = select(RawArticle.id).where(
        RawArticle.canonical_url == canonical_url
    )
    result = db.execute(stmt).scalar_one_or_none()
    return result


def check_near_duplicate(
    title_hash: str, semantic_hash: str, db: Session
) -> str | None:
    """title_hash 또는 semantic_hash로 근사 중복 검사."""
    stmt = select(RawArticle.id).where(
        (RawArticle.title_hash == title_hash)
        | (RawArticle.semantic_hash == semantic_hash)
    ).limit(1)
    result = db.execute(stmt).scalar_one_or_none()
    return result


# ── 이슈 후보 찾기 ──


def find_candidate_issues(
    keywords: list[str], window_hours: int, db: Session
) -> list[tuple[str, float]]:
    """키워드와 매칭되는 활성 이슈 목록을 (issue_id, 매칭 비율) 쌍으로 반환."""
    if not keywords:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    stmt = select(
        IssueKeywordState.issue_id,
        IssueKeywordState.normalized_keyword,
    ).where(
        IssueKeywordState.normalized_keyword.in_(keywords),
        IssueKeywordState.status.in_([
            KeywordLinkStatus.ACTIVE,
            KeywordLinkStatus.COOLDOWN,
        ]),
        IssueKeywordState.last_seen_at >= cutoff,
    )
    rows = db.execute(stmt).all()
    if not rows:
        return []

    # 이슈별 매칭 키워드 수 집계
    issue_matches: dict[str, int] = {}
    for issue_id, _ in rows:
        issue_matches[issue_id] = issue_matches.get(issue_id, 0) + 1

    total_keywords = len(keywords)
    return [
        (issue_id, match_count / total_keywords)
        for issue_id, match_count in sorted(
            issue_matches.items(), key=lambda x: x[1], reverse=True
        )
    ]


# ── 점수 계산 ──


def compute_match_score(
    article: dict, issue_id: str, keyword_ratio: float, db: Session
) -> float:
    """기사와 이슈 간 매칭 점수를 계산한다 (0.0 ~ 1.0)."""
    settings = get_settings()

    # 1) 키워드 점수: 매칭 비율 그대로
    keyword_score = keyword_ratio

    # 2) 엔티티 점수: 이슈에 연결된 기존 기사들의 엔티티와 비교
    entity_score = _compute_entity_score(article, issue_id, db)

    # 3) 시맨틱 점수: 이슈에 연결된 기존 기사 해시와 근접도
    semantic_score = _compute_semantic_score(article, issue_id, db)

    # 4) 시간 점수: 최근 기사일수록 높음
    time_score = _compute_time_score(article, issue_id, db)

    # 5) 출처 점수: 동일 출처에서 연속 보도 시 높음
    source_score = _compute_source_score(article, issue_id, db)

    total = (
        settings.classifier_weight_keyword * keyword_score
        + settings.classifier_weight_entity * entity_score
        + settings.classifier_weight_semantic * semantic_score
        + settings.classifier_weight_time * time_score
        + settings.classifier_weight_source * source_score
    )
    return min(total, 1.0)


def _compute_entity_score(article: dict, issue_id: str, db: Session) -> float:
    """기사의 엔티티와 이슈 기존 기사 엔티티 간 겹침 비율."""
    article_entities = _extract_entity_set(article.get("entity_json"))
    if not article_entities:
        return 0.0

    # 이슈에 연결된 기존 기사들의 엔티티 수집
    stmt = (
        select(RawArticle.entity_json)
        .join(EventUpdate, EventUpdate.article_id == RawArticle.id)
        .where(
            EventUpdate.issue_id == issue_id,
            EventUpdate.update_type != UpdateType.DUP,
            RawArticle.entity_json.isnot(None),
        )
        .limit(20)
    )
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return 0.3  # 첫 매칭 시 기본 점수

    issue_entities: set[str] = set()
    for entity_json in rows:
        issue_entities.update(_extract_entity_set(entity_json))

    if not issue_entities:
        return 0.3

    overlap = article_entities & issue_entities
    return len(overlap) / max(len(article_entities), 1)


def _extract_entity_set(entity_json: dict | list | None) -> set[str]:
    """엔티티 JSON에서 고유 엔티티 이름 집합을 추출."""
    if not entity_json:
        return set()
    entities: set[str] = set()
    if isinstance(entity_json, dict):
        for values in entity_json.values():
            if isinstance(values, list):
                entities.update(str(v).lower().strip() for v in values if v)
    elif isinstance(entity_json, list):
        entities.update(str(v).lower().strip() for v in entity_json if v)
    return entities


def _compute_semantic_score(article: dict, issue_id: str, db: Session) -> float:
    """시맨틱 해시 기반 근접도 (동일 해시 존재 시 높은 점수)."""
    semantic_hash = article.get("semantic_hash", "")
    title_hash = article.get("title_hash", "")

    stmt = (
        select(RawArticle.title_hash, RawArticle.semantic_hash)
        .join(EventUpdate, EventUpdate.article_id == RawArticle.id)
        .where(
            EventUpdate.issue_id == issue_id,
            EventUpdate.update_type != UpdateType.DUP,
        )
        .limit(50)
    )
    rows = db.execute(stmt).all()
    if not rows:
        return 0.2  # 첫 매칭 시 기본 점수

    for row_title_hash, row_semantic_hash in rows:
        if row_semantic_hash == semantic_hash:
            return 0.9
        if row_title_hash == title_hash:
            return 0.8

    return 0.2


def _compute_time_score(article: dict, issue_id: str, db: Session) -> float:
    """시간 근접도 점수. 이슈의 최근 기사와 시간 차이가 적을수록 높음."""
    stmt = (
        select(EventUpdate.created_at)
        .where(
            EventUpdate.issue_id == issue_id,
            EventUpdate.update_type != UpdateType.DUP,
        )
        .order_by(EventUpdate.created_at.desc())
        .limit(1)
    )
    latest = db.execute(stmt).scalar_one_or_none()
    if latest is None:
        return 0.5

    now = datetime.now(timezone.utc)
    hours_since = (now - latest).total_seconds() / 3600
    # 24시간 이내 → 0.9, 72시간 → 0.3
    if hours_since <= 24:
        return 0.9
    elif hours_since <= 48:
        return 0.6
    elif hours_since <= 72:
        return 0.3
    return 0.1


def _compute_source_score(article: dict, issue_id: str, db: Session) -> float:
    """동일 출처 연속 보도 점수."""
    source_name = (article.get("source_name") or "").lower().strip()
    if not source_name:
        return 0.3

    stmt = (
        select(RawArticle.source_name)
        .join(EventUpdate, EventUpdate.article_id == RawArticle.id)
        .where(
            EventUpdate.issue_id == issue_id,
            EventUpdate.update_type != UpdateType.DUP,
        )
        .limit(20)
    )
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return 0.3

    same_source = sum(
        1 for name in rows
        if name and name.lower().strip() == source_name
    )
    return min(0.3 + (same_source / len(rows)) * 0.7, 1.0)


# ── MAJOR 조건 감지 ──


_NUMBER_RE = re.compile(r"(\d[\d,.]*)\s*(명|건|원|억|만|%|천)")
_STATUS_PATTERNS = [
    (re.compile(r"검토.{0,5}확정", re.UNICODE), "status_confirmed"),
    (re.compile(r"수사.{0,5}기소", re.UNICODE), "status_prosecution"),
    (re.compile(r"계획.{0,5}시행", re.UNICODE), "status_enacted"),
    (re.compile(r"체포|구속|영장", re.UNICODE), "status_arrest"),
    (re.compile(r"사퇴|사임|해임|파면", re.UNICODE), "status_resign"),
    (re.compile(r"판결|선고", re.UNICODE), "status_ruling"),
    (re.compile(r"합의|타결", re.UNICODE), "status_settlement"),
]


def detect_major_reasons(article: dict, issue_id: str, db: Session) -> list[str]:
    """MAJOR_UPDATE를 정당화하는 구체적 근거를 감지한다."""
    reasons: list[str] = []
    title = article.get("title", "")
    content = article.get("content_text") or ""
    full_text = f"{title} {content}"

    # 1) 숫자 변화
    current_numbers = _NUMBER_RE.findall(full_text)
    if current_numbers:
        # 이슈의 기존 기사에서 숫자 추출하여 비교
        stmt = (
            select(RawArticle.title, RawArticle.content_text)
            .join(EventUpdate, EventUpdate.article_id == RawArticle.id)
            .where(
                EventUpdate.issue_id == issue_id,
                EventUpdate.update_type != UpdateType.DUP,
            )
            .order_by(EventUpdate.created_at.desc())
            .limit(5)
        )
        prev_rows = db.execute(stmt).all()
        prev_numbers: set[str] = set()
        for prev_title, prev_content in prev_rows:
            prev_text = f"{prev_title or ''} {prev_content or ''}"
            for num, unit in _NUMBER_RE.findall(prev_text):
                prev_numbers.add(f"{num}{unit}")

        for num, unit in current_numbers:
            if f"{num}{unit}" not in prev_numbers and prev_numbers:
                reasons.append("numeric_change")
                break

    # 2) 상태 변화 패턴
    for pattern, reason_tag in _STATUS_PATTERNS:
        if pattern.search(full_text):
            reasons.append(reason_tag)
            break  # 하나만 감지

    # 3) 핵심 주체 변화
    article_entities = _extract_entity_set(article.get("entity_json"))
    if article_entities:
        stmt = (
            select(RawArticle.entity_json)
            .join(EventUpdate, EventUpdate.article_id == RawArticle.id)
            .where(
                EventUpdate.issue_id == issue_id,
                EventUpdate.update_type != UpdateType.DUP,
                RawArticle.entity_json.isnot(None),
            )
            .order_by(EventUpdate.created_at.desc())
            .limit(5)
        )
        prev_entities_rows = db.execute(stmt).scalars().all()
        prev_entity_set: set[str] = set()
        for ej in prev_entities_rows:
            prev_entity_set.update(_extract_entity_set(ej))

        if prev_entity_set:
            new_entities = article_entities - prev_entity_set
            if new_entities and len(new_entities) / max(len(article_entities), 1) > 0.3:
                reasons.append("entity_change")

    return reasons


def _build_diff_summary(article: dict, reasons: list[str]) -> str:
    """MAJOR 근거에 기반한 요약 문자열 생성."""
    parts: list[str] = []
    title = article.get("title", "")

    if "numeric_change" in reasons:
        numbers = _NUMBER_RE.findall(f"{title} {article.get('content_text', '')}")
        if numbers:
            parts.append(f"수치 변화 감지: {numbers[0][0]}{numbers[0][1]}")

    status_reasons = [r for r in reasons if r.startswith("status_")]
    if status_reasons:
        parts.append(f"상태 변화 감지: {status_reasons[0]}")

    if "entity_change" in reasons:
        parts.append("새로운 핵심 주체 등장")

    return "; ".join(parts) if parts else ""


# ── 메인 분류 함수 ──


def classify_article(article: dict, db: Session) -> ClassificationResult:
    """기사 1건을 분류한다."""
    settings = get_settings()
    normalized = normalize_article(article)
    canonical_url = normalized["canonical_url"]
    title_hash = normalized["title_hash"]
    semantic_hash = normalized["semantic_hash"]

    # Step 1-2: 정확한 URL 중복 검사
    dup_id = check_exact_duplicate(canonical_url, db)
    if dup_id is not None:
        return ClassificationResult(
            article_id=dup_id,
            update_type=UpdateType.DUP,
            duplicate_of_id=dup_id,
        )

    # Step 3: 근사 중복 검사
    near_dup_id = check_near_duplicate(title_hash, semantic_hash, db)
    if near_dup_id is not None:
        return ClassificationResult(
            article_id=near_dup_id,
            update_type=UpdateType.DUP,
            duplicate_of_id=near_dup_id,
        )

    # Step 4: raw_articles에 INSERT
    now = datetime.now(timezone.utc)
    article_id = str(uuid4())
    published_at = normalized.get("published_at")
    if isinstance(published_at, str):
        try:
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            published_at = None

    raw = RawArticle(
        id=article_id,
        canonical_url=canonical_url,
        original_url=normalized["original_url"],
        title=normalized["title"],
        content_text=normalized.get("content_text"),
        source_name=normalized.get("source_name"),
        title_hash=title_hash,
        semantic_hash=semantic_hash,
        entity_json=normalized.get("entity_json"),
        normalized_keywords=normalized.get("normalized_keywords"),
        published_at=published_at,
        fetched_at=now,
        created_at=now,
    )
    db.add(raw)
    db.flush()

    # Step 5: 후보 이슈 매칭
    keywords = normalized.get("normalized_keywords") or []
    window_hours = settings.classifier_candidate_window_hours
    candidates = find_candidate_issues(keywords, window_hours, db)

    if not candidates:
        return ClassificationResult(
            article_id=article_id,
            update_type=UpdateType.NEW,
        )

    # Step 6: 최고 점수 후보로 매칭
    best_issue_id = None
    best_score = 0.0
    for issue_id, keyword_ratio in candidates:
        score = compute_match_score(normalized, issue_id, keyword_ratio, db)
        if score > best_score:
            best_score = score
            best_issue_id = issue_id

    # Step 7: 임계값 기반 분류
    if best_score < settings.classifier_score_new:
        return ClassificationResult(
            article_id=article_id,
            update_type=UpdateType.NEW,
            update_score=best_score,
        )

    if best_score >= settings.classifier_score_major:
        reasons = detect_major_reasons(normalized, best_issue_id, db)
        if reasons:
            diff = _build_diff_summary(normalized, reasons)
            return ClassificationResult(
                article_id=article_id,
                update_type=UpdateType.MAJOR_UPDATE,
                matched_issue_id=best_issue_id,
                update_score=best_score,
                major_reasons=reasons,
                diff_summary=diff,
            )

    # MINOR_UPDATE (score >= 0.45 또는 score >= 0.70 이지만 MAJOR 조건 미충족)
    return ClassificationResult(
        article_id=article_id,
        update_type=UpdateType.MINOR_UPDATE,
        matched_issue_id=best_issue_id,
        update_score=best_score,
    )


def classify_batch(articles: list[dict], db: Session) -> list[ClassificationResult]:
    """기사 목록을 일괄 분류한다.

    각 기사를 SAVEPOINT로 감싸서, 한 기사 실패 시 전체 트랜잭션이
    망가지지 않도록 한다.
    """
    results: list[ClassificationResult] = []
    for article in articles:
        try:
            nested = db.begin_nested()  # SAVEPOINT
            result = classify_article(article, db)
            nested.commit()
            results.append(result)
        except Exception as exc:
            db.rollback()  # SAVEPOINT rollback
            title = (article.get("title") or "")[:50]
            print(f"  [분류] 기사 분류 실패 ({title}): {exc}")
            continue
    return results
