"""외부 news-crawl-pipeline 프로젝트를 subprocess로 호출하는 래퍼."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.core.config import get_settings


def run_news_crawl(
    keywords: list[str],
    output_path: str | Path,
    report_path: str | Path | None = None,
    limit: int = 3,
    pipeline_dir: str | None = None,
) -> list[dict]:
    """외부 뉴스 파이프라인을 실행하여 기사를 수집한다.

    Args:
        keywords: 크롤링할 키워드 목록
        output_path: 기사 결과 JSON 출력 경로
        report_path: 크롤 리포트 JSON 출력 경로 (선택)
        limit: 키워드/채널당 기사 수
        pipeline_dir: 외부 파이프라인 디렉토리 (미지정 시 settings 사용)

    Returns:
        수집된 기사 목록 (list of dict)

    Raises:
        RuntimeError: 파이프라인 디렉토리 미설정 또는 실행 실패
    """
    settings = get_settings()
    pipe_dir = Path(pipeline_dir or settings.news_pipeline_dir)

    if not pipe_dir or not pipe_dir.is_dir():
        raise RuntimeError(
            f"news_pipeline_dir이 유효하지 않습니다: {pipe_dir}\n"
            "환경변수 NEWS_PIPELINE_DIR 또는 --pipeline-dir 옵션을 설정하세요."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "uv", "run", "news-pipeline",
        "--format", "json",
        "--out", str(output_path),
        "--limit", str(limit),
        "--no-spa",
    ]
    if report_path:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--report-out", str(report_path)])

    for kw in keywords:
        cmd.extend(["--keyword", kw])

    print(f"[크롤링] {' '.join(cmd[:8])}{'...' if len(cmd) > 8 else ''}")
    result = subprocess.run(cmd, cwd=pipe_dir, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        stderr_preview = result.stderr[:500] if result.stderr else "(no stderr)"
        raise RuntimeError(f"뉴스 크롤링 실패 (exit={result.returncode}): {stderr_preview}")

    with output_path.open("r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"[크롤링] {len(articles)}건 기사 수집 완료")
    return articles
