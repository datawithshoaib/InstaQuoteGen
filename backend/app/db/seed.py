"""Load the curated starter quotes the first time the app runs."""

import json
import logging
from pathlib import Path

from sqlmodel import Session, func, select

from app.db.models import Quote
from app.repositories.quotes import QuoteRepository

logger = logging.getLogger(__name__)


def seed_quotes(session: Session, seed_file: Path) -> int:
    if session.exec(select(func.count()).select_from(Quote)).one() > 0:
        return 0
    if not seed_file.exists():
        logger.warning("Seed file %s not found, starting with an empty library", seed_file)
        return 0

    raw = json.loads(seed_file.read_text(encoding="utf-8"))
    repo = QuoteRepository(session)
    added = 0
    for item in raw.get("quotes", []):
        text = (item.get("text") or "").strip()
        if not text:
            continue
        if repo.create(
            text=text,
            author=item.get("author"),
            tone=item.get("tone"),
            keywords=item.get("keywords", []),
            source="seed",
            commit=False,
        ):
            added += 1
    session.commit()
    logger.info("Seeded %d quotes from %s", added, seed_file.name)
    return added
