"""
education_extractor.py - Detects education qualifications from resume text.

Improvements:
  - Word-boundary regex matching instead of substring `in` operator.
  - Ambiguous short keywords (be, me, ba, ma) require education context
    (degree, university, year, grade) to avoid false positives.
  - Normalizes detected qualifications to canonical forms.
"""

import re
from utils.constants import EDUCATION_KEYWORDS

# Keywords that are safe for word-boundary matching (>= 3 chars, unambiguous)
_SAFE_KEYWORDS = [kw for kw in EDUCATION_KEYWORDS if len(kw) >= 3 and kw not in {"be", "me", "ba", "ma"}]

# Ambiguous 2-char keywords that need education context nearby
_AMBIGUOUS_KEYWORDS = {"be", "me", "ba", "ma"}

# Education context words — if any of these appear near the ambiguous keyword,
# it's likely an education reference, not common English
_EDU_CONTEXT_WORDS = [
    "degree", "engineering", "technology", "computer", "science", "university",
    "college", "institute", "cgpa", "gpa", "grade", "semester", "graduation",
    "graduated", "pursuing", "specialization", "stream", "branch",
    "mechanical", "electrical", "civil", "electronics", "information",
    "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
]

# Canonical normalization mapping for cleaner output
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
    """Check if keyword exists as a whole word/phrase in text."""
    pattern = r'(?<![a-zA-Z0-9.])' + re.escape(keyword) + r'(?![a-zA-Z0-9])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def _has_edu_context(text: str) -> bool:
    """Returns True if the text contains education-related context words."""
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in _EDU_CONTEXT_WORDS)


def extract_education(text: str) -> list:
    """
    Detects education qualifications using word-boundary matching.
    Ambiguous short keywords (be, me, ba, ma) require nearby education context.

    Returns a list of canonical education qualification strings.
    """
    if not text or not text.strip():
        return []

    found = set()

    # Pass 1: Safe keywords (unambiguous, >= 3 chars)
    for kw in _SAFE_KEYWORDS:
        if _word_boundary_match(kw, text):
            canonical = _EDU_CANONICAL.get(kw, kw)
            found.add(canonical)

    # Pass 2: Ambiguous short keywords — only if education context present
    if _has_edu_context(text):
        for kw in _AMBIGUOUS_KEYWORDS:
            if _word_boundary_match(kw, text):
                canonical = _EDU_CANONICAL.get(kw, kw)
                found.add(canonical)

    return sorted(found)
