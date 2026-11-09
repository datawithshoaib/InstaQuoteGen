from pydantic import Field, field_validator

from app.core.text import clean_quote_text
from app.schemas import ApiModel, UtcDatetime


class QuoteRead(ApiModel):
    id: int
    text: str
    author: str | None
    tone: str | None
    keywords: list[str]
    hashtags: list[str]
    reflection: str | None
    source: str
    quality_score: float | None
    run_id: str | None
    created_at: UtcDatetime


class QuoteCreate(ApiModel):
    text: str = Field(min_length=3, max_length=300)
    author: str | None = Field(default=None, max_length=80)
    tone: str | None = Field(default=None, max_length=30)
    keywords: list[str] = Field(default_factory=list, max_length=6)
    hashtags: list[str] = Field(default_factory=list, max_length=12)
    reflection: str | None = Field(default=None, max_length=300)
    source: str = Field(default="user", pattern="^(user|ai)$")
    quality_score: float | None = Field(default=None, ge=0, le=10)
    run_id: str | None = None

    @field_validator("text")
    @classmethod
    def _clean(cls, value: str) -> str:
        value = clean_quote_text(value)
        if len(value) < 3:
            raise ValueError("Quote text is too short")
        return value
