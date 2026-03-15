"""파이프라인 품질 게이트.

각 단계의 결과를 검증하고, 이상 시 경고 또는 사이클 조기 종료를 결정한다.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def validate_summary_json(raw: str, *, retry: bool = True) -> dict | None:
    """요약 응답 JSON 유효성 검증. 실패 시 retry=True이면 1회 재시도."""
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON 최상위가 dict가 아닙니다")
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(f"[quality_gate] 요약 JSON 유효성 실패: {exc}")
        if retry:
            return None  # 호출부에서 재시도 결정
        return None


def fallback_summary(title: str) -> dict:
    """LLM 실패 시 제목 기반 1문장 요약을 생성한다."""
    return {
        "summary": title,
        "tags": [],
        "fallback": True,
    }


def check_dup_ratio(stats: dict[str, int], *, threshold: float = 0.8) -> bool:
    """DUP 비율이 threshold 초과 시 True 반환 (사이클 조기 종료 권고).

    Returns:
        True이면 조기 종료 권고, False이면 정상 진행.
    """
    total = sum(stats.values())
    if total == 0:
        return False

    dup_count = stats.get("dup", 0)
    ratio = dup_count / total

    if ratio > threshold:
        logger.warning(
            f"[quality_gate] DUP 비율 {ratio:.1%} > {threshold:.0%} — "
            f"사이클 조기 종료 권고 (total={total}, dup={dup_count})"
        )
        return True
    return False


def check_collection_volume(
    current_count: int,
    recent_counts: list[int],
    *,
    threshold: float = 0.5,
) -> bool:
    """직전 사이클 대비 수집량이 threshold 이하이면 True (경고).

    Args:
        current_count: 이번 사이클 수집 건수.
        recent_counts: 직전 최대 3사이클의 수집 건수 목록.
        threshold: 평균 대비 비율 임계값.

    Returns:
        True이면 수집량 부족 경고, False이면 정상.
    """
    if not recent_counts:
        return False

    avg = sum(recent_counts) / len(recent_counts)
    if avg == 0:
        return False

    ratio = current_count / avg
    if ratio <= threshold:
        logger.warning(
            f"[quality_gate] 수집량 부족: 현재 {current_count}건, "
            f"최근 평균 {avg:.0f}건 (비율 {ratio:.1%} ≤ {threshold:.0%})"
        )
        return True
    return False


def check_source_health(
    channel_name: str,
    consecutive_failures: int,
    *,
    max_failures: int = 3,
) -> bool:
    """채널 연속 실패 횟수가 max_failures 이상이면 True (비활성화 권고).

    Returns:
        True이면 채널 비활성화 권고, False이면 정상.
    """
    if consecutive_failures >= max_failures:
        logger.warning(
            f"[quality_gate] 채널 '{channel_name}' 연속 {consecutive_failures}회 실패 — "
            f"비활성화 권고"
        )
        return True
    return False
