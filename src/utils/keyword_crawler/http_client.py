from __future__ import annotations

import asyncio
import random

import httpx

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

DEFAULT_HEADERS = {
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def _decode_body(raw: bytes, charset: str | None) -> str:
    for cs in [charset, "utf-8", "cp949", "euc-kr"]:
        if not cs:
            continue
        try:
            return raw.decode(cs, errors="strict")
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


class AsyncHttpClient:
    def __init__(self, timeout: float = 15.0, retries: int = 2, backoff: float = 0.5):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    async def get_text(self, url: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            headers = dict(DEFAULT_HEADERS)
            headers["User-Agent"] = random.choice(USER_AGENTS)
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=self.timeout,
                ) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    charset = resp.charset_encoding
                    return _decode_body(resp.content, charset)
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < self.retries:
                    await asyncio.sleep(self.backoff * (attempt + 1))
        raise RuntimeError(f"Fetch failed for {url}: {last_exc}") from last_exc
