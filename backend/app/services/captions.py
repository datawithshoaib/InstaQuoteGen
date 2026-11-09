"""Instagram caption builder.

Deterministic on purpose: the same quote always gets the same call to action,
so captions are reproducible and easy to test.
"""

import hashlib

from app.core.text import clean_tag

CALLS_TO_ACTION = [
    "Save this for the day you need it.",
    "Send this to someone who needs it today.",
    "Which line hit hardest? Tell me below.",
    "Read it twice. Then go do the thing.",
]
DEFAULT_TAGS = ["quotes", "dailyquotes", "mindset", "motivation"]
MAX_TAGS = 12


def build_caption(
    *,
    text: str,
    author: str | None = None,
    reflection: str | None = None,
    hashtags: list[str] | None = None,
    keywords: list[str] | None = None,
    photographer: str | None = None,
) -> str:
    digest = int(hashlib.sha1(text.encode()).hexdigest(), 16)
    cta = CALLS_TO_ACTION[digest % len(CALLS_TO_ACTION)]

    parts = [f"“{text}”"]
    if author:
        parts[0] += f"\n— {author}"
    if reflection:
        parts.append(reflection.strip())
    parts.append(cta)
    if photographer:
        parts.append(f"\U0001f4f7 Photo by {photographer} on Unsplash")

    tags: list[str] = []
    for raw in [*(hashtags or []), *(keywords or []), *DEFAULT_TAGS]:
        tag = clean_tag(raw)
        if len(tag) > 1 and tag not in tags:
            tags.append(tag)
    parts.append(" ".join(f"#{t}" for t in tags[:MAX_TAGS]))
    return "\n\n".join(parts)
