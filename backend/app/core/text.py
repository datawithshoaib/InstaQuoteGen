"""Small text helpers shared by the store and the AI guard rails."""

import re
import unicodedata

_WRAPPING_QUOTES = "\"'“”‘’«»"
_NON_WORD = re.compile(r"[^a-z0-9 ]+")
_SPACES = re.compile(r"\s+")


def clean_quote_text(text: str) -> str:
    """Trim whitespace and stray wrapping quotation marks."""
    text = _SPACES.sub(" ", unicodedata.normalize("NFKC", text)).strip()
    while len(text) > 1 and text[0] in _WRAPPING_QUOTES and text[-1] in _WRAPPING_QUOTES:
        text = text[1:-1].strip()
    return text


def text_key(text: str) -> str:
    """Normalised form used for duplicate detection ("Hello, World!" -> "hello world")."""
    lowered = clean_quote_text(text).lower().replace("’", "'")
    return _SPACES.sub(" ", _NON_WORD.sub(" ", lowered)).strip()


def clean_tag(tag: str) -> str:
    """'#Self Growth ' -> 'selfgrowth'."""
    return re.sub(r"[^\w]", "", tag.strip().lstrip("#").lower())


def word_count(text: str) -> int:
    return len(text.split())
