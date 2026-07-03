"""
cleaner.py - Cleans and normalizes raw extracted text.
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Cleans raw resume/JD text:
    - Preserves newlines (important for section detection)
    - Normalizes unicode but preserves tech characters (+, #, -)
    - Removes excess whitespace
    """
    if not text:
        return ""

    # Normalize unicode to closest ASCII-compatible form (NFC → NFKD decomposition)
    # This converts fancy quotes, dashes, accents to basic equivalents
    text = unicodedata.normalize("NFKD", text)

    # Manually fix common unicode that NFKD doesn't simplify well
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")   # en-dash, em-dash
    text = text.replace("\u2022", " ").replace("\u00b7", " ")   # bullet points

    # Remove control characters and non-printable chars,
    # but KEEP tech-relevant characters: +, #, -, ., /, @, etc.
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)

    # Collapse multiple spaces (not newlines)
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse more than 2 consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def clean_for_embedding(text: str) -> str:
    """
    Cleans text for embedding generation.
    Preserves compound skill names (hyphens, slashes) that are semantically important.
    """
    text = clean_text(text)
    text = text.lower()
    # Keep alphanumeric + tech chars that appear in skill names
    # +  → c++
    # #  → c#
    # .  → node.js, react.js
    # /  → ci/cd
    # -  → scikit-learn, fine-tuning
    # _  → some_skill
    text = re.sub(r"[^a-z0-9+#./\-_\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
