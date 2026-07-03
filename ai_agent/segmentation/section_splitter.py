"""
section_splitter.py - Splits resume text into logical sections using heading detection.

Improvements:
  - Strict heading detection: line must be short (< 40 chars) and heading must be a
    dominant keyword, not merely contained in a sentence.
  - Strips bullets, numbers, colons before matching to handle varied resume formatting.
  - Keywords sorted longest-first for deterministic matching.
"""

import re
from utils.constants import SECTION_KEYWORDS

# Characters commonly used as bullet points or list markers in resumes
_BULLET_RE = re.compile(r"^[\s\-\u2022\u2023\u25e6\u2043•·*>|#\d.)\]]+", re.UNICODE)


def _clean_heading_line(line: str) -> str:
    """Strips bullet markers, numbers, colons, and trailing punctuation from a line."""
    cleaned = _BULLET_RE.sub("", line)
    cleaned = cleaned.strip().rstrip(":").strip()
    return cleaned


def _is_heading_line(line: str, heading: str, cleaned: str) -> bool:
    """
    Returns True only if the line looks like a section heading, not regular content.

    Rules:
      1. Line must be short (< 40 chars after cleaning) — headings are brief.
      2. One of:
         a) Cleaned line exactly equals the heading keyword.
         b) Cleaned line starts with the heading keyword.
         c) The heading is a substantial part of the cleaned line (> 50% of chars).
    """
    if len(cleaned) > 40:
        return False

    cleaned_lower = cleaned.lower()

    # Exact match (most reliable)
    if cleaned_lower == heading:
        return True

    # Starts with heading + optional whitespace/punctuation
    if cleaned_lower.startswith(heading) and (
        len(cleaned_lower) == len(heading) or
        cleaned_lower[len(heading)] in " :-–—|/"
    ):
        return True

    # Heading is a dominant part of a short line
    # e.g. "Technical Skills" for heading "skills"
    if len(heading) >= 4 and heading in cleaned_lower:
        # Heading must be at least 50% of the line content
        if len(heading) / max(len(cleaned_lower), 1) >= 0.4:
            return True

    return False


def split_sections(text: str) -> dict:
    """
    Splits cleaned resume text into sections by detecting heading keywords.

    Returns a dict like:
    {
        "skills": "...",
        "experience": "...",
        "education": "...",
        "projects": "...",
        "certifications": "...",
        "summary": "...",
        "other": "..."
    }
    """
    # Build flat lookup: "technical skills" -> "skills"
    # Sort by keyword length descending for deterministic, longest-match-first behavior
    heading_pairs = []
    for section_key, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            heading_pairs.append((kw.lower(), section_key))
    heading_pairs.sort(key=lambda x: len(x[0]), reverse=True)

    sections = {key: "" for key in SECTION_KEYWORDS}
    sections["other"] = ""

    current_section = "other"
    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Try to match as a heading
        cleaned = _clean_heading_line(stripped)
        if not cleaned:
            sections[current_section] += line + "\n"
            continue

        matched_section = None
        for heading, section_key in heading_pairs:
            if _is_heading_line(stripped, heading, cleaned):
                matched_section = section_key
                break

        if matched_section:
            current_section = matched_section
        else:
            sections[current_section] += line + "\n"

    return sections


def get_full_text_sections(sections: dict) -> str:
    """Joins all section text into a single string for full-text operations."""
    return "\n".join(sections.values())
