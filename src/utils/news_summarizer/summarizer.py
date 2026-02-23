"""뉴스 요약 핵심 로직: LLM 호출, 결과 파싱, 매칭, DB 저장."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.utils.news_summarizer.llm_client import SYSTEM_PROMPT, call_ollama, create_ollama_client
from src.utils.news_summarizer.prompt_builder import (
    build_combined_prompt,
    group_by_keyword,
    load_articles,
)


def _clean_json_response(raw: str) -> dict:
    """LLM 응답에서 JSON을 파싱한다.

    gemma3:4b 등 경량 모델의 다양한 응답 형태를 처리:
    - 마크다운 코드블록 래핑 제거
    - 배열 응답 → {"keywords": [...]} 정규화
    - {"keywords": [...], "articles": [...]} 등 비표준 구조 처리
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    data = json.loads(cleaned)

    # Case 1: 배열 응답 [{"keyword": ..., "summary": ...}, ...]
    if isinstance(data, list):
        merged: list[dict] = []
        for item in data:
            if isinstance(item, dict) and "keyword" in item and "summary" in item:
                merged.append(item)
            elif isinstance(item, dict) and "keywords" in item:
                # [{"keywords": [...]}, ...] 중첩 배열
                merged.extend(item["keywords"])
        return {"keywords": merged}

    # Case 2: {"keywords": [str, ...], "articles": [...]} — 키워드가 문자열 배열인 경우
    if isinstance(data, dict) and "keywords" in data:
        kw_list = data["keywords"]
        if kw_list and isinstance(kw_list[0], str):
            # articles 배열에서 요약 정보를 추출하여 키워드와 매칭
            articles = data.get("articles", [])
            merged = []
            for article in articles:
                if isinstance(article, dict) and "summary" in article:
                    merged.append(article)
            if merged:
                return {"keywords": merged}
            # articles도 없으면 빈 결과
            return {"keywords": []}

    return data


def run_summarize(input_path: str, output_path: str, model: str | None = None) -> dict:
    """뉴스 기사를 요약하고 결과를 JSON으로 저장한다.

    Args:
        input_path: 뉴스 크롤링 결과 JSON/JSONL 파일 경로
        output_path: 요약 결과 출력 JSON 경로
        model: Ollama 모델명 (미지정 시 settings 기본값)

    Returns:
        요약 결과 dict
    """
    articles = load_articles(input_path)
    if not articles:
        print("[ERROR] 입력 파일에 기사가 없습니다.", file=sys.stderr)
        sys.exit(1)

    groups = group_by_keyword(articles)
    client, model = create_ollama_client(model)

    print(f"[INFO] {len(articles)}건 기사, {len(groups)}개 키워드 로드 완료")
    print(f"[INFO] Ollama 모델: {model}")
    print("[INFO] 전체 키워드를 1회 요청으로 통합 처리합니다")

    combined_prompt = build_combined_prompt(groups)
    print(f"[INFO] 통합 프롬프트 크기: {len(combined_prompt):,}자")
    print("[API ] 요약 요청 중...", end=" ", flush=True)

    raw = ""
    try:
        raw, usage = call_ollama(client, model, SYSTEM_PROMPT, combined_prompt)
        parsed = _clean_json_response(raw)
        print(f"OK ({usage['prompt']}+{usage['completion']} tokens)")
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패 ({e}), 원본 저장")
        # 디버그용: raw 응답 파일에 별도 저장
        raw_path = Path(output_path).with_suffix(".raw.txt")
        raw_path.write_text(raw, encoding="utf-8")
        parsed = {"keywords": [], "_raw_response": raw[:2000]}
        usage = {"prompt": 0, "completion": 0}
    except Exception as exc:
        print(f"FAIL: {exc}")
        parsed = {"keywords": [], "error": str(exc)[:500]}
        usage = {"prompt": 0, "completion": 0}

    # LLM 응답의 키워드 요약 목록
    llm_items = [
        item for item in parsed.get("keywords", [])
        if isinstance(item, dict) and item.get("summary")
    ]
    print(f"[INFO] LLM 요약 {len(llm_items)}건 파싱됨")

    # 키워드별 매핑: 정확 매칭 → 부분 매칭(포함 관계) → 순서 매칭
    input_keywords = list(groups.keys())
    llm_summaries: dict[str, dict] = {}

    for item in llm_items:
        # keyword 필드 또는 title 필드에서 키워드 추출
        kw = item.get("keyword", "") or item.get("title", "")
        if kw:
            llm_summaries[kw] = item

    # 정확 매칭 시도
    matched: dict[str, dict] = {}
    for kw in input_keywords:
        if kw in llm_summaries:
            matched[kw] = llm_summaries[kw]

    # 정확 매칭 실패 시 부분 매칭 (입력 키워드가 LLM 키워드에 포함되거나 반대)
    if len(matched) < len(input_keywords):
        unmatched_inputs = [k for k in input_keywords if k not in matched]
        unmatched_llm = [
            (k, v) for k, v in llm_summaries.items()
            if v not in matched.values()
        ]
        for inp_kw in unmatched_inputs:
            for llm_kw, llm_data in unmatched_llm:
                if inp_kw in llm_kw or llm_kw in inp_kw:
                    matched[inp_kw] = llm_data
                    unmatched_llm = [(k, v) for k, v in unmatched_llm if k != llm_kw]
                    break

    # 그래도 안 되면 순서대로 매칭
    if len(matched) < len(input_keywords) and len(llm_items) >= len(input_keywords):
        still_unmatched = [k for k in input_keywords if k not in matched]
        used_items = set(id(v) for v in matched.values())
        remaining_items = [item for item in llm_items if id(item) not in used_items]
        for kw, item in zip(still_unmatched, remaining_items):
            matched[kw] = item

    print(f"[INFO] 키워드 매핑: {len(matched)}/{len(input_keywords)} 성공")
    if matched:
        for kw in input_keywords:
            status = "OK" if kw in matched else "MISS"
            print(f"  [{status}] {kw}")

    # 최종 출력 구성: LLM 요약 + 원본 기사 목록 병합
    keyword_results: list[dict] = []
    for keyword, kw_articles in groups.items():
        llm_data = matched.get(keyword, {})
        keyword_results.append({
            "keyword": keyword,
            "article_count": len(kw_articles),
            "summary": llm_data.get("summary", ""),
            "key_points": llm_data.get("key_points", []),
            "sentiment": llm_data.get("sentiment", "neutral"),
            "category": llm_data.get("category", "society"),
            # entities를 tags의 fallback으로 사용 (gemma3가 tags 대신 entities를 반환하는 경우)
            "tags": llm_data.get("tags") or llm_data.get("entities", []),
            "articles": [
                {
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "channel": a.get("channel", ""),
                    "confidence": a.get("confidence", 0),
                }
                for a in kw_articles
            ],
        })

    output = {
        "summarized_at": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "provider": "ollama",
        "model": model,
        "api_calls": 1,
        "total_keywords": len(groups),
        "total_articles": len(articles),
        "total_tokens": {
            "prompt": usage["prompt"],
            "completion": usage["completion"],
            "total": usage["prompt"] + usage["completion"],
        },
        "keywords": keyword_results,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return output


# ── DB 저장 ─────────────────────────────────────────────────


def save_to_db(result: dict, db_url: str | None = None) -> str:
    """요약 결과를 PostgreSQL에 저장한다. 생성된 batch_id를 반환."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.db.news_summary import NewsSummaryBatch, NewsKeywordSummary, NewsSummaryTag

    if db_url:
        engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    else:
        from src.db.session import SessionLocal

    now = datetime.now(timezone.utc)
    batch_id = str(uuid.uuid4())

    batch = NewsSummaryBatch(
        id=batch_id,
        provider=result["provider"],
        model=result["model"],
        total_keywords=result["total_keywords"],
        total_articles=result["total_articles"],
        prompt_tokens=result["total_tokens"]["prompt"],
        completion_tokens=result["total_tokens"]["completion"],
        summarized_at=datetime.fromisoformat(result["summarized_at"].rstrip("Z")),
        created_at=now,
    )

    for kw_data in result["keywords"]:
        summary_id = str(uuid.uuid4())
        summary = NewsKeywordSummary(
            id=summary_id,
            batch_id=batch_id,
            keyword=kw_data["keyword"],
            summary=kw_data["summary"],
            key_points=kw_data.get("key_points"),
            sentiment=kw_data.get("sentiment", "neutral"),
            category=kw_data.get("category", "society"),
            article_count=kw_data.get("article_count", 0),
            articles=kw_data.get("articles"),
            created_at=now,
        )
        batch.summaries.append(summary)

        for tag_name in kw_data.get("tags", []):
            tag = NewsSummaryTag(
                id=str(uuid.uuid4()),
                summary_id=summary_id,
                tag=tag_name.strip()[:50],
                created_at=now,
            )
            summary.tags.append(tag)

    session = SessionLocal()
    try:
        session.add(batch)
        session.commit()
        print(f"[DB  ] 저장 완료: batch_id={batch_id}")
        print(f"  요약 {len(batch.summaries)}건, 태그 총 "
              f"{sum(len(s.tags) for s in batch.summaries)}개")
        return batch_id
    except Exception as exc:
        session.rollback()
        print(f"[DB  ] 저장 실패: {exc}", file=sys.stderr)
        raise
    finally:
        session.close()
