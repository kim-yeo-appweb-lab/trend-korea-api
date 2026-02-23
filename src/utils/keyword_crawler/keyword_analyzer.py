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

# 명사구 추출을 위한 POS 태그 설정
NOUN_TAGS = frozenset({"NNG", "NNP"})  # 일반명사, 고유명사
# 명사 사이에서 연결 역할을 하는 태그 (조사, 접미사)
BRIDGE_TAGS = frozenset(
    {"JKS", "JKO", "JKB", "JKG", "JKC", "JX", "JC", "XSN"}
)
MAX_PHRASE_NOUNS = 4  # 하나의 구에 포함될 최대 명사 수


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


def _extract_noun_groups(tokens: list) -> list[list[tuple[str, str]]]:
    """토큰 시퀀스에서 근접 명사 그룹을 (form, tag) 리스트로 추출한다.

    명사(NNG/NNP)가 조사 하나를 사이에 두고 연속되면 같은 그룹으로 묶는다.
    예: "트럼프가 관세를 부과" → [("트럼프","NNP"), ("관세","NNG"), ("부과","NNG")]
    """
    groups: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    saw_bridge = False

    for token in tokens:
        if (
            token.tag in NOUN_TAGS
            and len(token.form) >= MIN_KEYWORD_LEN
            and token.form not in STOPWORDS
        ):
            current.append((token.form, token.tag))
            saw_bridge = False
        elif current and token.tag in BRIDGE_TAGS and not saw_bridge:
            saw_bridge = True
        else:
            if current:
                groups.append(current)
                current = []
            saw_bridge = False

    if current:
        groups.append(current)
    return groups


def _phrases_from_group(group: list[tuple[str, str]]) -> list[str]:
    """명사 그룹에서 바이그램~MAX_PHRASE_NOUNS 크기의 명사구를 생성한다.

    단일 명사 그룹은 고유명사(NNP)인 경우만 반환한다.
    """
    forms = [f for f, _ in group]
    n = len(forms)

    if n == 1:
        # 고유명사만 단독 키워드로 허용 (일반명사 단독은 맥락 부족)
        if group[0][1] == "NNP":
            return [forms[0]]
        return []

    phrases: list[str] = []
    for size in range(2, min(MAX_PHRASE_NOUNS, n) + 1):
        for i in range(n - size + 1):
            phrases.append(" ".join(forms[i : i + size]))
    return phrases


def _filter_subphrases(
    ranked: list[tuple[str, int]], top_n: int
) -> list[tuple[str, int]]:
    """상위 랭크 구에 포함되는 하위 구를 제거한다.

    "트럼프 관세 부과"(count=5)가 이미 있으면
    "관세 부과"(count=5)는 중복이므로 제거. 단, 하위 구의 빈도가
    상위 구보다 훨씬 높으면(다른 맥락에서도 등장) 유지한다.
    """
    filtered: list[tuple[str, int]] = []

    for phrase, count in ranked:
        if len(filtered) >= top_n:
            break

        is_dominated = False
        words = set(phrase.split())
        for accepted_phrase, accepted_count in filtered:
            accepted_words = set(accepted_phrase.split())
            # 단어 집합이 완전히 포함되고, 빈도가 비슷하면 중복으로 간주
            if phrase != accepted_phrase and (
                words < accepted_words or words > accepted_words or phrase in accepted_phrase
            ):
                if count <= accepted_count * 1.5:
                    is_dominated = True
                    break

        if not is_dominated:
            filtered.append((phrase, count))

    return filtered


def extract_keywords(texts: list[str], top_n: int = 30) -> list[KeywordResult]:
    """kiwipiepy 형태소 분석으로 명사구 키워드를 추출한다.

    단일 명사 대신 근접 명사를 묶어 문맥을 파악할 수 있는
    짧은 구(예: "트럼프 관세 부과", "올림픽 유치")를 생성한다.
    고유명사(NNP)는 단독으로도 유지한다.
    """
    kiwi = _get_kiwi()
    counter: Counter[str] = Counter()

    for text in texts:
        result = kiwi.analyze(text)
        if not result:
            continue
        tokens, _ = result[0]
        groups = _extract_noun_groups(tokens)

        seen: set[str] = set()  # 한 헤드라인에서 동일 구 중복 카운트 방지
        for group in groups:
            for phrase in _phrases_from_group(group):
                if phrase not in seen:
                    counter[phrase] += 1
                    seen.add(phrase)

    # 후보를 넉넉히 뽑은 뒤, 하위 구를 필터링
    candidates = counter.most_common(top_n * 3)
    result_pairs = _filter_subphrases(candidates, top_n)

    return [
        KeywordResult(word=phrase, count=count, rank=i + 1)
        for i, (phrase, count) in enumerate(result_pairs)
    ]


def extract_keywords_simple(texts: list[str], top_n: int = 30) -> list[KeywordResult]:
    """정규식 기반 폴백 (kiwipiepy 없을 때). 단일 명사만 추출."""
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
