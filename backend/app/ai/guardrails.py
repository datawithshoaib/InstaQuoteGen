"""Deterministic guard rails around the LLM.

Input rails run before any model call. Output rails run on every draft
before the LLM judge sees it. They are cheap, predictable and unit-tested,
which is exactly what you want in front of (and behind) a non-deterministic
model.
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from app.ai.prompts import BANNED_CLICHES
from app.core.text import clean_quote_text, text_key, word_count

MIN_WORDS = 5
MAX_WORDS = 28
SIMILARITY_THRESHOLD = 0.82

_INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|prompts?)",
    r"disregard (all |the )?(previous|prior|above)",
    r"system prompt",
    r"you are now",
    r"act as (an? )?(ai|assistant|model|dan)",
    r"</?(system|topic|tone|avoid|feedback|quotes)>",
    r"```",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)
_ALLOWED_TOPIC_RE = re.compile(r"^[\w\s,&'’.\-!?/]+$", re.UNICODE)
_URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
_EMOJI_RE = re.compile("[\U0001f300-\U0001faff☀-➿]")


class InputRejected(ValueError):
    """Raised when user input fails an input guard rail."""


def check_topic(topic: str) -> str:
    """Validate and normalise a user-supplied topic. Raises InputRejected."""
    topic = re.sub(r"\s+", " ", topic or "").strip()
    if len(topic) < 2:
        raise InputRejected("Topic is too short.")
    if len(topic) > 80:
        raise InputRejected("Keep the topic under 80 characters.")
    if _INJECTION_RE.search(topic):
        raise InputRejected("That topic looks like an instruction to the AI. Describe a theme instead.")
    if not _ALLOWED_TOPIC_RE.match(topic):
        raise InputRejected("Use letters, numbers and basic punctuation only.")
    return topic


@dataclass
class DraftCheck:
    text: str
    passed: bool
    reasons: list[str] = field(default_factory=list)


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, text_key(a), text_key(b)).ratio()


def check_draft(text: str, existing: list[str]) -> DraftCheck:
    """Rule-based checks on a single drafted quote."""
    cleaned = clean_quote_text(text)
    reasons: list[str] = []

    words = word_count(cleaned)
    if words < MIN_WORDS:
        reasons.append(f"too short ({words} words)")
    elif words > MAX_WORDS:
        reasons.append(f"too long ({words} words)")

    if "#" in cleaned:
        reasons.append("contains a hashtag")
    if _URL_RE.search(cleaned):
        reasons.append("contains a link")
    if _EMOJI_RE.search(cleaned):
        reasons.append("contains an emoji")

    lowered = cleaned.lower()
    cliches = [c for c in BANNED_CLICHES if c in lowered]
    if cliches:
        reasons.append(f"uses a cliché ('{cliches[0]}')")

    key = text_key(cleaned)
    for other in existing:
        if text_key(other) == key or similarity(cleaned, other) >= SIMILARITY_THRESHOLD:
            reasons.append("too close to an existing quote")
            break

    return DraftCheck(text=cleaned, passed=not reasons, reasons=reasons)
