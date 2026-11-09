from typing import Any, Literal

from pydantic import Field, field_validator

from app.ai.guardrails import InputRejected, check_topic
from app.schemas import ApiModel, UtcDatetime

TONES = ("Inspirational", "Stoic", "Bold", "Poetic", "Calm", "Playful", "Melancholic", "Witty")
Tone = Literal["Inspirational", "Stoic", "Bold", "Poetic", "Calm", "Playful", "Melancholic", "Witty"]


class GenerationRequest(ApiModel):
    topic: str = Field(min_length=2, max_length=80, examples=["discipline"])
    tone: Tone = "Inspirational"
    count: int = Field(default=3, ge=1, le=6)

    @field_validator("topic")
    @classmethod
    def _guard_topic(cls, value: str) -> str:
        try:
            return check_topic(value)
        except InputRejected as exc:
            raise ValueError(str(exc)) from exc


class GeneratedQuote(ApiModel):
    text: str
    author: str | None = None
    tone: str | None = None
    angle: str | None = None
    keywords: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    reflection: str | None = None
    score: float | None = None
    scores: dict[str, int] | None = None
    library_id: int | None = None


class Usage(ApiModel):
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0


class GenerationResponse(ApiModel):
    run_id: str
    status: Literal["success", "partial", "fallback", "error"]
    source: Literal["llm", "library"]
    model: str | None
    prompt_version: str
    quotes: list[GeneratedQuote]
    visual_mood: list[str] = Field(default_factory=list)
    rounds: int
    latency_ms: int
    usage: Usage
    note: str | None = None


class RunSummary(ApiModel):
    id: str
    topic: str
    tone: str
    requested_count: int
    status: str
    source: str
    model: str | None
    prompt_version: str
    rounds: int
    llm_calls: int
    input_tokens: int
    output_tokens: int
    latency_ms: int
    avg_score: float | None
    accepted_count: int
    rejected_count: int
    error: str | None
    created_at: UtcDatetime


class RunDetail(RunSummary):
    steps: list[dict[str, Any]]
    results: list[dict[str, Any]]


class RunStats(ApiModel):
    total_runs: int
    by_status: dict[str, int]
    avg_latency_ms: int | None
    avg_score: float | None
    total_input_tokens: int
    total_output_tokens: int
    acceptance_rate: float | None
