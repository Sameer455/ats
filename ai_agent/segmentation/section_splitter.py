import re
from utils.constants import SECTION_KEYWORDS

_BULLET_RE = re.compile(r"^[\s\-\u2022\u2023\u25e6\u2043•·*>|#\d.)\]]+", re.UNICODE)


def _clean_heading_line(line: str) -> str:
    cleaned = _BULLET_RE.sub("", line)
    cleaned = cleaned.strip().rstrip(":").strip()
    return cleaned


def _is_heading_line(line: str, heading: str, cleaned: str) -> bool:
    if len(cleaned) > 40:
        return False

    cleaned_lower = cleaned.lower()

    if cleaned_lower == heading:
        return True

    if cleaned_lower.startswith(heading) and (
        len(cleaned_lower) == len(heading) or
        cleaned_lower[len(heading)] in " :-–—|/"
    ):
        return True

    if len(heading) >= 4 and heading in cleaned_lower:
        if len(heading) / max(len(cleaned_lower), 1) >= 0.4:
            return True

    return False


def split_sections(text: str) -> dict:
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
    return "\n".join(sections.values())
