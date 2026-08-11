import re
from utils.constants import ROLES


def _role_boundary_match(role: str, text: str) -> bool:
    pattern = r'(?<![a-zA-Z])' + re.escape(role) + r'(?![a-zA-Z])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def extract_roles(text: str) -> list:
    if not text or not text.strip():
        return []

    found_roles = set()

    for role in sorted(ROLES, key=len, reverse=True):
        if _role_boundary_match(role, text):
            found_roles.add(role)

    return sorted(found_roles)
