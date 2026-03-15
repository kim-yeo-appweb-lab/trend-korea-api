"""Crontab 기반 개별 잡 실행 CLI.

사용법:
    trend-korea-cron <job_name>                        잡 단독 실행 (DB 저장)
    trend-korea-cron news_collect --top-n 30 --limit 5 테스트 모드 (JSON 출력)
    trend-korea-cron --list                            등록된 잡 목록 출력
"""

from __future__ import annotations

import argparse
import sys

from src.scheduler.runner import run_job

# ── 잡 레지스트리 ──
# (잡 이름, 핸들러 함수, 설명)

JOB_REGISTRY: dict[str, tuple[str, str]] = {
    "keyword_collect": (
        "src.scheduler.jobs.pipeline_jobs:collect_keywords",
        "트렌드 키워드 수집 → DB 저장",
    ),
    "news_collect": (
        "src.scheduler.jobs.pipeline_jobs:run_news_collect_cycle",
        "키워드 수집 → 뉴스 크롤링 → 분류 → 요약",
    ),
    "keyword_state_cleanup": (
        "src.scheduler.jobs.pipeline_jobs:cleanup_keyword_states",
        "이슈 키워드 상태 정리 (ACTIVE→COOLDOWN→CLOSED)",
    ),
    "issue_status_reconcile": (
        "src.scheduler.jobs.issue_jobs:reconcile_issue_status",
        "이슈 상태 조정",
    ),
    "search_rankings": (
        "src.scheduler.jobs.search_jobs:recalculate_search_rankings",
        "검색 랭킹 재계산",
    ),
    "community_hot_score": (
        "src.scheduler.jobs.community_jobs:recalculate_community_hot_score",
        "인기 게시글 점수 업데이트",
    ),
    "cleanup_refresh_tokens": (
        "src.scheduler.jobs.auth_jobs:cleanup_refresh_tokens",
        "만료된 리프레시 토큰 정리",
    ),
    "issue_rankings": (
        "src.scheduler.jobs.feed_jobs:calculate_issue_rankings",
        "이슈 랭킹 스냅샷 계산 (Top Stories)",
    ),
}


def _resolve_handler(dotted_path: str):
    """'module.path:function_name' 형식의 핸들러를 동적 임포트한다."""
    module_path, func_name = dotted_path.rsplit(":", 1)
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def _run_pipeline_test(args: argparse.Namespace) -> None:
    """테스트 모드: DB 저장 없이 파이프라인 실행, JSON 결과를 stdout에 출력한다."""
    import json
    from datetime import datetime, timezone
    from pathlib import Path

    from src.core.config import get_settings
    from src.utils.pipeline.orchestrator import run_cycle

    settings = get_settings()
    project_root = Path(__file__).resolve().parent.parent.parent
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cycle_dir = project_root / "cycle_outputs" / f"test_{timestamp}"

    result = run_cycle(
        cycle_num=1,
        cycle_dir=cycle_dir,
        top_n=args.top_n or 30,
        max_keywords=args.max_keywords or 5,
        limit=args.limit or 3,
        model=args.model,
        use_naver=bool(settings.naver_api_client),
        keyword_strategy="intersection",
        enable_classification=True,
        save_db=False,
    )

    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="trend-korea-cron",
        description="Crontab 기반 개별 잡 실행 CLI",
    )
    parser.add_argument(
        "job_name",
        nargs="?",
        help="실행할 잡 이름",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_jobs",
        help="등록된 잡 목록 출력",
    )

    # ── 파이프라인 테스트 매개변수 (news_collect 전용) ──
    parser.add_argument(
        "--top-n", type=int, default=None, help="키워드 수집 상위 N개 (기본: 30)"
    )
    parser.add_argument(
        "--max-keywords", type=int, default=None, help="사용할 키워드 수 (기본: 5)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="키워드당 기사 수 (기본: 3)"
    )
    parser.add_argument("--model", type=str, default=None, help="Ollama 모델명")

    args = parser.parse_args()

    if args.list_jobs:
        print(f"{'잡 이름':<30} {'설명'}")
        print("-" * 70)
        for name, (_, desc) in sorted(JOB_REGISTRY.items()):
            print(f"{name:<30} {desc}")
        return

    if not args.job_name:
        parser.print_help()
        sys.exit(1)

    if args.job_name not in JOB_REGISTRY:
        print(f"알 수 없는 잡: {args.job_name}")
        print(f"등록된 잡: {', '.join(sorted(JOB_REGISTRY))}")
        sys.exit(1)

    # 로깅 설정
    from src.core.logging import configure_logging

    configure_logging()

    # 파이프라인 테스트 모드: 매개변수가 하나라도 있으면 JSON 출력 (DB 저장 안 함)
    pipeline_params = [args.top_n, args.max_keywords, args.limit, args.model]
    if args.job_name == "news_collect" and any(p is not None for p in pipeline_params):
        _run_pipeline_test(args)
        return

    # 프로덕션 모드: DB 저장 + JobRun 기록
    dotted_path, _ = JOB_REGISTRY[args.job_name]
    handler = _resolve_handler(dotted_path)
    run_job(args.job_name, handler)


if __name__ == "__main__":
    main()
