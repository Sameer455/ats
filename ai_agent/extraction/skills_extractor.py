import re
from utils.constants import SKILLS_DB, SKILL_SYNONYMS

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

_MIN_SKILL_LEN = 2


def _strict_word_boundary(skill: str, text: str) -> bool:
    escaped = re.escape(skill)
    pattern = r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def _apply_synonyms(skill: str) -> str:
    return SKILL_SYNONYMS.get(skill.lower().strip(), skill.lower().strip())


def _detect_r_language(text: str) -> bool:
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

    if re.search(r'(?<![a-zA-Z])\bR\b(?![a-zA-Z])', text):
        context_words = {"python", "java", "sql", "matlab", "sas", "spss",
                         "statistics", "data analysis", "machine learning"}
        text_lower = text.lower()
        context_count = sum(1 for w in context_words if w in text_lower)
        if context_count >= 2:
            return True

    return False


def extract_skills(text: str) -> list:
    if not text or not text.strip():
        return []

    found = set()

    for skill in sorted(SKILLS_DB, key=len, reverse=True):
        if len(skill) < _MIN_SKILL_LEN:
            continue
        if _strict_word_boundary(skill, text):
            canonical = _apply_synonyms(skill)
            found.add(canonical)

    for alias, canonical in SKILL_SYNONYMS.items():
        if len(alias) >= 3 and _strict_word_boundary(alias, text):
            found.add(canonical)

    tokens = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.\-]*\b', text))
    tokens_lower = {t.lower() for t in tokens}
    for alias, canonical in _ALIASES.items():
        if alias in tokens_lower:
            found.add(canonical)

    if _detect_r_language(text):
        found.add("r")

    return sorted(found)
