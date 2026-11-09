"""Structured-output contracts for each LLM call.

The LLM never returns free text to us. Every call is bound to one of these
Pydantic models, so a malformed answer fails loudly instead of leaking into
the product.
"""

from pydantic import BaseModel, Field


class Plan(BaseModel):
    angles: list[str] = Field(
        description="3 to 5 distinct, specific angles on the topic. A few words each.",
    )
    visual_mood: list[str] = Field(
        description="3 to 5 concrete photo-search phrases that fit the mood, e.g. 'foggy pine forest'.",
    )


class DraftQuote(BaseModel):
    text: str = Field(
        description="The quote. 6 to 25 words. No hashtags, emojis or surrounding quotation marks.",
    )
    angle: str = Field(description="Which planned angle this quote explores.")
    keywords: list[str] = Field(
        description="2 to 4 concrete visual keywords for a background photo, e.g. 'empty road'.",
    )
    hashtags: list[str] = Field(description="4 to 8 relevant Instagram hashtags, without '#'.")
    reflection: str = Field(
        description="One short sentence (max 25 words) for the caption that expands the idea.",
    )


class DraftBatch(BaseModel):
    quotes: list[DraftQuote]


class QuoteReview(BaseModel):
    index: int = Field(description="Index of the quote being reviewed, as given in the input.")
    originality: int = Field(ge=1, le=10, description="1 = cliché or a known quote, 10 = fresh.")
    clarity: int = Field(ge=1, le=10, description="1 = confusing, 10 = instantly understood.")
    impact: int = Field(ge=1, le=10, description="1 = flat, 10 = makes you stop scrolling.")
    on_topic: int = Field(ge=1, le=10, description="1 = unrelated, 10 = squarely on the topic.")
    safe: bool = Field(description="False if hateful, sexual, violent, harassing or harmful.")
    feedback: str = Field(description="One sentence on how the quote could be stronger.")


class ReviewBatch(BaseModel):
    reviews: list[QuoteReview]
