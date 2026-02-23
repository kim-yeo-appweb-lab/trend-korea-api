"""Ollama LLM 클라이언트 및 시스템 프롬프트."""

from __future__ import annotations

from src.core.config import get_settings

SYSTEM_PROMPT = """\
뉴스 기사를 키워드별로 요약하세요.
반드시 순수 JSON 배열만 출력하세요. 마크다운 코드블록(```)을 쓰지 마세요.

[
  {
    "keyword": "입력 키워드 그대로",
    "summary": "이슈 배경, 현재 상황, 전망을 포함한 상세 요약 (300자 이상)",
    "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "sentiment": "positive 또는 negative 또는 neutral 또는 mixed 중 하나",
    "category": "politics 또는 economy 또는 society 또는 international 또는 culture 또는 technology 중 하나",
    "tags": ["관련 태그1", "관련 태그2", "관련 태그3"]
  }
]

반드시 지킬 것:
1. keyword는 입력에 있는 키워드를 그대로 복사
2. summary는 한글 300자 이상으로 상세하게 작성
3. key_points는 3개 이상, 각각 한 문장
4. tags는 인물명, 기관명, 핵심 주제어를 3~7개
5. 입력에 없는 키워드를 추가하지 말 것
"""


def create_ollama_client(model: str | None = None) -> tuple:
    """Ollama OpenAI-compatible 클라이언트를 생성한다.

    Returns:
        (client, model_name) 튜플
    """
    from openai import OpenAI

    settings = get_settings()
    base_url = settings.ollama_base_url
    model = model or settings.ollama_default_model
    client = OpenAI(api_key="ollama", base_url=base_url)
    return client, model


def call_ollama(client, model: str, system: str, user: str) -> tuple[str, dict]:
    """Ollama에 요약 요청을 보낸다. (응답 텍스트, 토큰 사용량) 반환."""
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    text = r.choices[0].message.content or "{}"
    usage = {
        "prompt": r.usage.prompt_tokens if r.usage else 0,
        "completion": r.usage.completion_tokens if r.usage else 0,
    }
    return text, usage
