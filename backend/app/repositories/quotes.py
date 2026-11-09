from collections.abc import Sequence

from sqlalchemy import String, cast
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, func, or_, select

from app.core.text import clean_quote_text, clean_tag, text_key
from app.db.models import Quote


class QuoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, quote_id: int) -> Quote | None:
        return self.session.get(Quote, quote_id)

    def exists(self, text: str) -> bool:
        stmt = select(Quote.id).where(Quote.text_key == text_key(text))
        return self.session.exec(stmt).first() is not None

    def create(
        self,
        *,
        text: str,
        author: str | None = None,
        tone: str | None = None,
        keywords: Sequence[str] = (),
        hashtags: Sequence[str] = (),
        reflection: str | None = None,
        source: str = "user",
        quality_score: float | None = None,
        run_id: str | None = None,
        commit: bool = True,
    ) -> Quote | None:
        """Insert a quote. Returns None when an equivalent quote already exists."""
        text = clean_quote_text(text)
        if self.exists(text):
            return None
        quote = Quote(
            text=text,
            text_key=text_key(text),
            author=(author or "").strip() or None,
            tone=(tone or "").strip() or None,
            keywords=[k.strip().lower() for k in keywords if k and k.strip()][:6],
            hashtags=[t for t in (clean_tag(h) for h in hashtags) if t][:10],
            reflection=reflection,
            source=source,
            quality_score=quality_score,
            run_id=run_id,
        )
        self.session.add(quote)
        if commit:
            try:
                self.session.commit()
            except IntegrityError:  # lost a race with a concurrent insert
                self.session.rollback()
                return None
            self.session.refresh(quote)
        else:
            self.session.flush()
        return quote

    def delete(self, quote: Quote) -> None:
        self.session.delete(quote)
        self.session.commit()

    def page(
        self,
        *,
        search: str | None = None,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Quote], int]:
        stmt = select(Quote)
        if search:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Quote.text).like(pattern),
                    func.lower(func.coalesce(Quote.author, "")).like(pattern),
                    func.lower(func.coalesce(Quote.tone, "")).like(pattern),
                    # keywords is a JSON list; a LIKE on its text form is fine at this scale.
                    func.lower(cast(Quote.keywords, String)).like(pattern),
                )
            )
        if source:
            stmt = stmt.where(Quote.source == source)
        total = self.session.exec(select(func.count()).select_from(stmt.subquery())).one()
        items = self.session.exec(
            stmt.order_by(col(Quote.created_at).desc(), col(Quote.id).desc()).offset(offset).limit(limit)
        ).all()
        return list(items), total

    def random(self) -> Quote | None:
        return self.session.exec(select(Quote).order_by(func.random()).limit(1)).first()

    def all(self) -> list[Quote]:
        return list(self.session.exec(select(Quote)).all())

    def count(self) -> int:
        return self.session.exec(select(func.count()).select_from(Quote)).one()
