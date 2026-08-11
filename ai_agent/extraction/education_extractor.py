import re
from utils.constants import EDUCATION_KEYWORDS

_SAFE_KEYWORDS = [kw for kw in EDUCATION_KEYWORDS if len(kw) >= 3 and kw not in {"be", "me", "ba", "ma"}]

_AMBIGUOUS_KEYWORDS = {"be", "me", "ba", "ma"}

_EDU_CONTEXT_WORDS = [
    "degree", "engineering", "technology", "computer", "science", "university",
    "college", "institute", "cgpa", "gpa", "grade", "semester", "graduation",
    "graduated", "pursuing", "specialization", "stream", "branch",
    "mechanical", "electrical", "civil", "electronics", "information",
    "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
]

_EDU_CANONICAL = {
    "b.tech": "B.Tech", "btech": "B.Tech",
    "b.e": "B.E", "be": "B.E",
    "b.sc": "B.Sc", "bsc": "B.Sc",
    "b.a": "B.A", "ba": "B.A",
    "m.tech": "M.Tech", "mtech": "M.Tech",
    "m.e": "M.E", "me": "M.E",
    "m.sc": "M.Sc", "msc": "M.Sc",
    "m.a": "M.A", "ma": "M.A",
    "mba": "MBA",
    "phd": "Ph.D", "ph.d": "Ph.D", "doctorate": "Ph.D",
    "bachelor": "Bachelor's", "master": "Master's",
    "associate": "Associate", "diploma": "Diploma",
}


def _word_boundary_match(keyword: str, text: str) -> bool:
    pattern = r'(?<![a-zA-Z0-9.])' + re.escape(keyword) + r'(?![a-zA-Z0-9])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def _has_edu_context(text: str) -> bool:
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in _EDU_CONTEXT_WORDS)


def extract_education(text: str) -> list:
    if not text or not text.strip():
        return []

    found = set()

    for kw in _SAFE_KEYWORDS:
        if _word_boundary_match(kw, text):
            canonical = _EDU_CANONICAL.get(kw, kw)
            found.add(canonical)

    if _has_edu_context(text):
        for kw in _AMBIGUOUS_KEYWORDS:
            if _word_boundary_match(kw, text):
                canonical = _EDU_CANONICAL.get(kw, kw)
                found.add(canonical)

    return sorted(found)
