"""Database tables.

SQLite is enough for a single-user studio and gives us stable ids, unique
constraints and atomic writes, all things the old JSON file could not.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return uuid4().hex


class Quote(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str
    # Normalised text, used to stop the same quote being stored twice.
    text_key: str = Field(index=True, unique=True)
    author: str | None = None
    tone: str | None = None
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    hashtags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    reflection: str | None = None
    source: str = Field(default="user", index=True)  # seed | user | ai
    quality_score: float | None = None
    run_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Background(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    source: str  # unsplash | gradient
    aspect_ratio: str
    width: int
    height: int
    filename: str
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    palette: str | None = None
    photographer_name: str | None = None
    photographer_url: str | None = None
    photo_url: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Post(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    filename: str
    aspect_ratio: str
    width: int
    height: int
    quote_text: str
    quote_author: str | None = None
    caption: str
    background_source: str
    photographer_name: str | None = None
    photographer_url: str | None = None
    style: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, index=True)


class GenerationRun(SQLModel, table=True):
    """One execution of the AI pipeline, kept for observability and debugging."""

    id: str = Field(default_factory=new_id, primary_key=True)
    topic: str
    tone: str
    requested_count: int
    status: str = Field(index=True)  # success | partial | fallback | error
    source: str  # llm | library
    model: str | None = None
    prompt_version: str
    rounds: int = 0
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    avg_score: float | None = None
    accepted_count: int = 0
    rejected_count: int = 0
    error: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    results: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, index=True)
