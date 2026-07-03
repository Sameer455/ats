"""
skills_extractor.py - Accurate skill extraction using multi-pass hybrid approach.

Strategies (in order of reliability):
  1. Exact phrase matching with strict word-boundary regex (longest-first)
  2. Synonym expansion — alternate spellings in text mapped to canonical names
  3. Safe alias table — only unambiguous abbreviations (ML, DL, NLP, k8s, etc.)
  4. Special handling for ambiguous single-char skills (R language)
"""

import re
from utils.constants import SKILLS_DB, SKILL_SYNONYMS

# ──────────────────────────────────────────────────────────────────────────────
# Safe alias table: ONLY unambiguous abbreviations
# Removed: oop, os, cd, bi, vc, vcs, swe, sde, qa (too many false positives)
# ──────────────────────────────────────────────────────────────────────────────
_ALIASES = {
    "ml":    "machine learning",
    "dl":    "deep learning",
    "cv":    "computer vision",
    "rl":    "reinforcement learning",
    "nlp":   "nlp",
    "etl":   "etl",
    "elt":   "elt",
    "rag":   "rag",
    "llm":   "llm",
    "llms":  "llms",
    "k8s":   "kubernetes",
    "tf":    "tensorflow",
    "mlops": "mlops",
}

# Minimum skill length for SKILLS_DB matching (single chars like "r" are too ambiguous)
_MIN_SKILL_LEN = 2


def _strict_word_boundary(skill: str, text: str) -> bool:
    """
    Word-boundary match with proper handling of special regex chars (c++, c#, node.js).
    Uses negative lookbehind/lookahead to prevent partial matches.
    """
    escaped = re.escape(skill)
    pattern = r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def _apply_synonyms(skill: str) -> str:
    """Maps a skill string through the synonym table to get the canonical form."""
    return SKILL_SYNONYMS.get(skill.lower().strip(), skill.lower().strip())


def _detect_r_language(text: str) -> bool:
    """
    Special detection for R programming language.
    Only matches when:
      - Uppercase standalone "R" appears near programming context words
      - Or explicit "R programming", "R language", "R studio", "RStudio"
    """
    # Explicit mentions — high confidence
    explicit_patterns = [
        r'\bR\s+programming\b',
        r'\bR\s+language\b',
        r'\bR\s*Studio\b',
        r'\bRStudio\b',
        r'\bR\s+statistical\b',
        r'\bR\s+for\s+data\b',
        r'\bcran\b',
        r'\bggplot2?\b',
        r'\btidyverse\b',
        r'\bdplyr\b',
        r'\bshiny\b',
    ]
    for pat in explicit_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True

    # Standalone uppercase "R" near tech context
    # Must be uppercase and surrounded by comma-separated skills or listed skills
    if re.search(r'(?<![a-zA-Z])\bR\b(?![a-zA-Z])', text):
        # Check if it's in a skills-list context (near other known skills)
        context_words = {"python", "java", "sql", "matlab", "sas", "spss",
                         "statistics", "data analysis", "machine learning"}
        text_lower = text.lower()
        context_count = sum(1 for w in context_words if w in text_lower)
        if context_count >= 2:
            return True

    return False


def extract_skills(text: str) -> list:
    """
    Extracts skills from text using a multi-pass hybrid approach.

    Pass 1: Exact phrase match against SKILLS_DB (longest-first, skip single-char).
    Pass 2: Synonym key scan (skip very short aliases).
    Pass 3: Safe alias match (whole-token only, unambiguous abbreviations).
    Pass 4: Special R language detection.

    Returns a deduplicated, sorted list of canonical skill names.
    """
    if not text or not text.strip():
        return []

    found = set()

    # ── Pass 1: SKILLS_DB exact phrase match ─────────────────────────────────
    for skill in sorted(SKILLS_DB, key=len, reverse=True):
        # Skip single-character skills (too ambiguous for regex matching)
        if len(skill) < _MIN_SKILL_LEN:
            continue
        if _strict_word_boundary(skill, text):
            canonical = _apply_synonyms(skill)
            found.add(canonical)

    # ── Pass 2: Synonym key scan ─────────────────────────────────────────────
    for alias, canonical in SKILL_SYNONYMS.items():
        if len(alias) >= 3 and _strict_word_boundary(alias, text):
            found.add(canonical)

    # ── Pass 3: Safe alias table (whole-token only) ──────────────────────────
    tokens = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.\-]*\b', text))
    tokens_lower = {t.lower() for t in tokens}
    for alias, canonical in _ALIASES.items():
        if alias in tokens_lower:
            found.add(canonical)

    # ── Pass 4: Special R language detection ─────────────────────────────────
    if _detect_r_language(text):
        found.add("r")

    return sorted(found)
