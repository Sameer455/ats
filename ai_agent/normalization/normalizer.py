"""
normalizer.py - Normalizes and deduplicates extracted skill lists.
"""

from utils.constants import SKILL_SYNONYMS


def normalize_skills(skills: list) -> list:
    """
    Applies synonym normalization to a list of extracted skills and deduplicates.
    """
    normalized = set()
    for skill in skills:
        skill_lower = skill.lower().strip()
        canonical = SKILL_SYNONYMS.get(skill_lower, skill_lower)
        normalized.add(canonical)
    return sorted(normalized)


def normalize_text_skill(skill: str) -> str:
    """Normalizes a single skill string."""
    skill_lower = skill.lower().strip()
    return SKILL_SYNONYMS.get(skill_lower, skill_lower)
