"""LLM access for the pipeline.

The graph talks to a small `QuoteLLM` interface instead of a chat model
directly. That keeps provider details in one place and lets tests and evals
swap in a deterministic fake without patching LangChain internals.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.ai import prompts
from app.ai.schemas import DraftBatch, Plan, ReviewBatch
from app.core.config import Settings


class LLMError(RuntimeError):
    """The model call failed or returned something we could not parse."""


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMResult[T]:
    value: T
    usage: Usage = field(default_factory=Usage)
    latency_ms: int = 0


class QuoteLLM(Protocol):
    model_name: str

    async def plan(self, *, topic: str, tone: str) -> LLMResult[Plan]: ...

    async def write(
        self,
        *,
        topic: str,
        tone: str,
        angles: list[str],
        count: int,
        avoid: list[str],
        feedback: list[str],
    ) -> LLMResult[DraftBatch]: ...

    async def review(self, *, topic: str, tone: str, quotes: list[str]) -> LLMResult[ReviewBatch]: ...


def _bullets(items: list[str], empty: str = "(none)") -> str:
    return "\n".join(f"- {item}" for item in items) if items else empty


class LangChainQuoteLLM:
    """QuoteLLM backed by any LangChain chat model that supports structured output."""

    def __init__(self, writer: BaseChatModel, judge: BaseChatModel, model_name: str):
        self._writer = writer
        self._judge = judge
        self.model_name = model_name

    async def _call[T: BaseModel](
        self,
        model: BaseChatModel,
        prompt: ChatPromptTemplate,
        schema: type[T],
        variables: dict[str, Any],
    ) -> LLMResult[T]:
        chain = prompt | model.with_structured_output(schema, include_raw=True)
        started = time.perf_counter()
        try:
            out = await chain.ainvoke(variables)
        except Exception as exc:  # network, auth, rate limit, timeout...
            raise LLMError(f"{type(exc).__name__}: {exc}") from exc
        latency = int((time.perf_counter() - started) * 1000)

        parsed = out.get("parsed")
        if out.get("parsing_error") or parsed is None:
            raise LLMError(f"Model output did not match {schema.__name__}: {out.get('parsing_error')}")

        meta = getattr(out.get("raw"), "usage_metadata", None) or {}
        usage = Usage(meta.get("input_tokens", 0), meta.get("output_tokens", 0))
        return LLMResult(parsed, usage, latency)

    async def plan(self, *, topic: str, tone: str) -> LLMResult[Plan]:
        return await self._call(self._writer, prompts.PLANNER, Plan, {"topic": topic, "tone": tone})

    async def write(self, *, topic, tone, angles, count, avoid, feedback) -> LLMResult[DraftBatch]:
        return await self._call(
            self._writer,
            prompts.WRITER,
            DraftBatch,
            {
                "topic": topic,
                "tone": tone,
                "angles": ", ".join(angles),
                "count": count,
                "avoid": _bullets(avoid),
                "feedback": _bullets(feedback, empty="(first attempt)"),
                "cliches": "; ".join(prompts.BANNED_CLICHES),
            },
        )

    async def review(self, *, topic, tone, quotes) -> LLMResult[ReviewBatch]:
        numbered = "\n".join(f"[{i}] {q}" for i, q in enumerate(quotes))
        return await self._call(
            self._judge,
            prompts.JUDGE,
            ReviewBatch,
            {"topic": topic, "tone": tone, "quotes": numbered},
        )


def build_llm(settings: Settings) -> QuoteLLM | None:
    """Create the LLM client, or None when no API key is configured."""
    if settings.llm_provider == "fake":
        from app.ai.fake_llm import FakeQuoteLLM

        return FakeQuoteLLM(model_name="fake-llm (demo)", latency_seconds=0.7)
    if not settings.llm_enabled:
        return None
    from langchain_groq import ChatGroq

    def make(temperature: float) -> ChatGroq:
        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=temperature,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    return LangChainQuoteLLM(
        writer=make(settings.writer_temperature),
        judge=make(settings.judge_temperature),
        model_name=settings.groq_model,
    )
