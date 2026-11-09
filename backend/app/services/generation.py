"""Runs the quote pipeline and records what happened.

Responsibilities:
* choose between the LLM pipeline and the offline library fallback,
* enforce an overall time budget,
* stream progress events to the caller,
* persist a GenerationRun for observability, whatever the outcome.
"""

import asyncio
import logging
import random
import re
import time
from collections.abc import AsyncIterator
from typing import Any

from sqlmodel import Session
from starlette.concurrency import run_in_threadpool

from app.ai.graph import run_pipeline
from app.ai.llm import QuoteLLM
from app.ai.prompts import PROMPT_VERSION
from app.ai.tracing import Emit, RunTracer
from app.core.config import Settings
from app.db.engine import get_engine
from app.db.models import GenerationRun, Quote, new_id
from app.repositories.quotes import QuoteRepository
from app.repositories.runs import RunRepository
from app.schemas.generation import GeneratedQuote, GenerationRequest, GenerationResponse, Usage

logger = logging.getLogger(__name__)

_WORD = re.compile(r"[a-z]+")
_DONE = object()


class GenerationService:
    def __init__(self, settings: Settings, llm: QuoteLLM | None):
        self.settings = settings
        self.llm = llm

    # ------------------------------------------------------------------ public

    async def generate(self, req: GenerationRequest, emit: Emit | None = None) -> GenerationResponse:
        tracer = RunTracer(emit=emit) if emit else RunTracer()
        run_id = new_id()
        started = time.perf_counter()
        library = await run_in_threadpool(self._load_library)

        await tracer.event(
            "run",
            {
                "run_id": run_id,
                "topic": req.topic,
                "tone": req.tone,
                "count": req.count,
                "mode": "llm" if self.llm else "library",
                "model": self.llm.model_name if self.llm else None,
                "prompt_version": PROMPT_VERSION,
            },
        )

        quotes: list[dict[str, Any]] = []
        source, status = "library", "fallback"
        error: str | None = None
        note: str | None = None
        rounds = accepted = rejected = 0
        mood: list[str] = []

        if self.llm is not None:
            try:
                out = await asyncio.wait_for(
                    run_pipeline(
                        llm=self.llm,
                        tracer=tracer,
                        topic=req.topic,
                        tone=req.tone,
                        count=req.count,
                        avoid=[q.text for q in library][-200:],
                        min_score=self.settings.min_quality_score,
                        max_rewrite_rounds=self.settings.max_rewrite_rounds,
                    ),
                    timeout=self.settings.pipeline_timeout_seconds,
                )
                quotes, rounds, mood = out.quotes, out.rounds, out.visual_mood
                accepted, rejected = out.accepted, out.rejected
                if quotes:
                    source = "llm"
                    status = "success" if len(quotes) >= req.count else "partial"
                    if status == "partial":
                        note = (
                            f"Only {len(quotes)} of {req.count} drafts cleared the quality bar "
                            f"({self.settings.min_quality_score:.1f}/10)."
                        )
            except TimeoutError:
                error = f"Pipeline exceeded {self.settings.pipeline_timeout_seconds:.0f}s"
                logger.warning("Run %s timed out", run_id)
            except Exception as exc:  # any LLM/provider failure -> graceful fallback
                error = str(exc)[:500]
                logger.warning("Run %s failed, falling back to library: %s", run_id, exc)

        if not quotes:
            async with tracer.step("library", "Picking from your library") as step:
                quotes = self._pick_from_library(library, req)
                step.detail = f"{len(quotes)} matching quotes"
            if self.llm is None:
                note = "AI generation is off (no GROQ_API_KEY), so these come from your library."
            else:
                note = "The AI pipeline did not return usable quotes, so these come from your library."
            if error:
                status = "error" if not quotes else "fallback"

        latency_ms = int((time.perf_counter() - started) * 1000)
        response = GenerationResponse(
            run_id=run_id,
            status=status,
            source=source,
            model=self.llm.model_name if self.llm else None,
            prompt_version=PROMPT_VERSION,
            quotes=[GeneratedQuote(**q) for q in quotes],
            visual_mood=mood,
            rounds=rounds,
            latency_ms=latency_ms,
            usage=Usage(
                input_tokens=tracer.input_tokens,
                output_tokens=tracer.output_tokens,
                llm_calls=tracer.llm_calls,
            ),
            note=note,
        )
        await run_in_threadpool(self._save_run, response, req, tracer, accepted, rejected, error)
        logger.info(
            "Run %s %s via %s: %d quotes, %d rounds, %d ms, %d tokens",
            run_id,
            status,
            source,
            len(quotes),
            rounds,
            latency_ms,
            tracer.input_tokens + tracer.output_tokens,
        )
        return response

    async def stream(self, req: GenerationRequest) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        """Yield (event, data) pairs while the run progresses, ending with the result."""
        queue: asyncio.Queue[Any] = asyncio.Queue()

        async def emit(name: str, data: dict[str, Any]) -> None:
            await queue.put((name, data))

        async def worker() -> GenerationResponse:
            try:
                return await self.generate(req, emit=emit)
            finally:
                await queue.put(_DONE)

        task = asyncio.create_task(worker())
        try:
            while (item := await queue.get()) is not _DONE:
                yield item
            result = await task
            yield "result", result.model_dump(mode="json")
        except Exception as exc:
            logger.exception("Streaming run failed")
            yield "error", {"message": str(exc) or "Generation failed"}
        finally:
            if not task.done():  # client disconnected mid-run
                task.cancel()

    # ----------------------------------------------------------------- helpers

    def _load_library(self) -> list[Quote]:
        with Session(get_engine()) as session:
            return QuoteRepository(session).all()

    def _pick_from_library(self, library: list[Quote], req: GenerationRequest) -> list[dict]:
        if not library:
            return []
        topic_words = set(_WORD.findall(req.topic.lower()))

        def relevance(q: Quote) -> float:
            haystack = set(_WORD.findall(f"{q.text} {' '.join(q.keywords)} {q.tone or ''}".lower()))
            overlap = len(topic_words & haystack)
            tone_bonus = 0.5 if (q.tone or "").lower() == req.tone.lower() else 0
            return overlap + tone_bonus + random.random() * 0.3  # light shuffle among ties

        ranked = sorted(library, key=relevance, reverse=True)[: req.count]
        return [
            {
                "text": q.text,
                "author": q.author,
                "tone": q.tone or req.tone,
                "keywords": q.keywords,
                "hashtags": q.hashtags or [*q.keywords, "quotes"],
                "reflection": q.reflection,
                "score": q.quality_score,
                "library_id": q.id,
            }
            for q in ranked
        ]

    def _save_run(
        self,
        response: GenerationResponse,
        req: GenerationRequest,
        tracer: RunTracer,
        accepted: int,
        rejected: int,
        error: str | None,
    ) -> None:
        scores = [q.score for q in response.quotes if q.score is not None and response.source == "llm"]
        run = GenerationRun(
            id=response.run_id,
            topic=req.topic,
            tone=req.tone,
            requested_count=req.count,
            status=response.status,
            source=response.source,
            model=response.model,
            prompt_version=response.prompt_version,
            rounds=response.rounds,
            llm_calls=tracer.llm_calls,
            input_tokens=tracer.input_tokens,
            output_tokens=tracer.output_tokens,
            latency_ms=response.latency_ms,
            avg_score=round(sum(scores) / len(scores), 2) if scores else None,
            accepted_count=accepted,
            rejected_count=rejected,
            error=error,
            steps=[s.as_dict() for s in tracer.steps],
            results=[q.model_dump() for q in response.quotes],
        )
        with Session(get_engine()) as session:
            RunRepository(session).add(run)
