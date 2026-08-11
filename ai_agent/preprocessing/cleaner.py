import re
import unicodedata


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)

    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2022", " ").replace("\u00b7", " ")

    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def clean_for_embedding(text: str) -> str:
    text = clean_text(text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#./\-_\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
