"""뉴스 기사 로드 및 프롬프트 구성."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

MAX_ARTICLES_PER_KEYWORD = 3
MAX_CONTENT_CHARS = 500


def load_articles(input_path: str) -> list[dict]:
    """JSON 또는 JSONL 파일에서 기사 목록을 로드한다."""
    path = Path(input_path)
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def group_by_keyword(articles: list[dict]) -> dict[str, list[dict]]:
    """기사를 키워드별로 그룹핑한다."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        groups[article["keyword"]].append(article)
    for kw in groups:
        groups[kw].sort(key=lambda a: -a.get("confidence", 0))
    return dict(groups)


def build_combined_prompt(groups: dict[str, list[dict]]) -> str:
    """모든 키워드의 기사를 하나의 프롬프트로 합친다."""
    parts = [f"총 {len(groups)}개 키워드에 대한 뉴스 기사입니다.\n"]

    for keyword, articles in groups.items():
        selected = articles[:MAX_ARTICLES_PER_KEYWORD]
        parts.append(f'{"=" * 50}')
        parts.append(f'[키워드: "{keyword}"] 관련 기사 {len(selected)}건')
        parts.append(f'{"=" * 50}')

        for i, article in enumerate(selected, 1):
            title = article.get("title", "(제목 없음)")
            content = article.get("content_text", "")[:MAX_CONTENT_CHARS]
            channel = article.get("channel", "")
            parts.append(f"\n--- 기사 {i} [{channel}] ---")
            parts.append(f"제목: {title}")
            if content:
                parts.append(f"본문: {content}")

        parts.append("")

    return "\n".join(parts)
