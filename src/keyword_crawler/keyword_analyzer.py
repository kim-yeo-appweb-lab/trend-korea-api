from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

_kiwi = None

STOPWORDS = frozenset(
    {
        "것",
        "수",
        "등",
        "년",
        "월",
        "일",
        "때",
        "중",
        "후",
        "전",
        "내",
        "더",
        "곳",
        "외",
        "위",
        "말",
        "점",
        "그",
        "이",
        "저",
        "뉴스",
        "기자",
        "특파원",
        "사진",
        "영상",
        "속보",
        "단독",
        "종합",
        "오늘",
        "어제",
        "내일",
        "현재",
        "관련",
        "대해",
        "모두",
        "매우",
        "사이",
        "최근",
        "지금",
        "통해",
        "대한",
        "또한",
        "이번",
    }
)

MIN_KEYWORD_LEN = 2


@dataclass(slots=True)
class KeywordResult:
    word: str
    count: int
    rank: int


def _get_kiwi():
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi

        _kiwi = Kiwi()
    return _kiwi


def extract_keywords(texts: list[str], top_n: int = 30) -> list[KeywordResult]:
    """kiwipiepy 형태소 분석으로 한국어 명사 키워드를 추출한다."""
    kiwi = _get_kiwi()
    counter: Counter[str] = Counter()

    for text in texts:
        result = kiwi.analyze(text)
        if not result:
            continue
        tokens, _ = result[0]
        for token in tokens:
            if token.tag in ("NNG", "NNP") and len(token.form) >= MIN_KEYWORD_LEN:
                if token.form not in STOPWORDS:
                    counter[token.form] += 1

    return [
        KeywordResult(word=word, count=count, rank=i + 1)
        for i, (word, count) in enumerate(counter.most_common(top_n))
    ]


def extract_keywords_simple(texts: list[str], top_n: int = 30) -> list[KeywordResult]:
    """정규식 기반 폴백 (kiwipiepy 없을 때)."""
    counter: Counter[str] = Counter()
    pattern = re.compile(r"[\uAC00-\uD7AF]{2,}")
    for text in texts:
        for match in pattern.finditer(text):
            word = match.group()
            if word not in STOPWORDS and len(word) >= MIN_KEYWORD_LEN:
                counter[word] += 1
    return [
        KeywordResult(word=word, count=count, rank=i + 1)
        for i, (word, count) in enumerate(counter.most_common(top_n))
    ]
