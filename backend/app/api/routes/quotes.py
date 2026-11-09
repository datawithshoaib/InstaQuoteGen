from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import SessionDep
from app.core.errors import ConflictError, NotFoundError
from app.repositories.quotes import QuoteRepository
from app.schemas import Page
from app.schemas.quotes import QuoteCreate, QuoteRead

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("", response_model=Page[QuoteRead])
def list_quotes(
    session: SessionDep,
    search: Annotated[str | None, Query(max_length=100)] = None,
    source: Annotated[str | None, Query(pattern="^(seed|user|ai)$")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = QuoteRepository(session).page(search=search, source=source, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
def create_quote(payload: QuoteCreate, session: SessionDep):
    quote = QuoteRepository(session).create(**payload.model_dump())
    if quote is None:
        raise ConflictError("That quote is already in your library.")
    return quote


@router.get("/random", response_model=QuoteRead)
def random_quote(session: SessionDep):
    quote = QuoteRepository(session).random()
    if quote is None:
        raise NotFoundError("Your library is empty.")
    return quote


@router.get("/{quote_id}", response_model=QuoteRead)
def get_quote(quote_id: int, session: SessionDep):
    quote = QuoteRepository(session).get(quote_id)
    if quote is None:
        raise NotFoundError("Quote not found.")
    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(quote_id: int, session: SessionDep) -> None:
    repo = QuoteRepository(session)
    quote = repo.get(quote_id)
    if quote is None:
        raise NotFoundError("Quote not found.")
    repo.delete(quote)
