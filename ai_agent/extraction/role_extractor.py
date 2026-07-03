"""
role_extractor.py - Extracts job roles/titles from resume text.

Uses word-boundary regex matching instead of substring `in` to prevent
false positives like "sre" matching inside "desire".
"""

import re
from utils.constants import ROLES


def _role_boundary_match(role: str, text: str) -> bool:
    """Word-boundary match for job role phrases."""
    pattern = r'(?<![a-zA-Z])' + re.escape(role) + r'(?![a-zA-Z])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def extract_roles(text: str) -> list:
    """
    Detects known job roles from resume text using word-boundary matching.
    Longer, more specific roles are matched first to avoid conflicts.
    """
    if not text or not text.strip():
        return []

    found_roles = set()

    # Sort by length descending: "machine learning engineer" before "software engineer"
    for role in sorted(ROLES, key=len, reverse=True):
        if _role_boundary_match(role, text):
            found_roles.add(role)

    return sorted(found_roles)
