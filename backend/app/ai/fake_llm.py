"""A deterministic stand-in for the real LLM.

Used by the test suite and by `evals --fake`, so the whole pipeline (graph,
guard rails, retries, tracing, API, streaming) can be exercised offline and
for free. It deliberately produces a few bad drafts so the review and
rewrite loop actually gets used.
"""

import asyncio
from dataclasses import dataclass, field

from app.ai.llm import LLMResult, Usage
from app.ai.schemas import DraftBatch, DraftQuote, Plan, QuoteReview, ReviewBatch

_GOOD_LINES = [
    "The quiet work you do at dawn becomes the loud result everyone notices later.",
    "Your pace is not slow, it is simply yours. Keep walking the road you chose.",
    "Some doors only open after you stop knocking and start building your own house.",
    "Calm is not the absence of storms, it is knowing where your anchor is.",
    "Small honest steps carry you further than big promises you never keep.",
    "Rest is part of the climb, not a detour from it.",
    "What you repeat in private is what you become in public.",
    "Let the old version of you be proud, not comfortable.",
]


@dataclass
class FakeQuoteLLM:
    model_name: str = "fake-llm"
    # Make one first-round draft a cliché so the guard rails reject it.
    inject_bad_draft: bool = True
    fail_on: str | None = None  # "plan" | "write" | "review" to simulate an outage
    latency_seconds: float = 0.0  # simulated model latency, so the live UI has something to show
    calls: list[str] = field(default_factory=list)
    _cursor: int = 0

    async def _maybe_fail(self, step: str) -> None:
        self.calls.append(step)
        if self.latency_seconds:
            await asyncio.sleep(self.latency_seconds)
        if self.fail_on == step:
            from app.ai.llm import LLMError

            raise LLMError(f"simulated {step} failure")

    async def plan(self, *, topic: str, tone: str) -> LLMResult[Plan]:
        await self._maybe_fail("plan")
        plan = Plan(
            angles=[f"{topic} in small daily habits", f"{topic} when nobody is watching", "patience"],
            visual_mood=["misty mountain", "empty road at dawn", "calm ocean"],
        )
        return LLMResult(plan, Usage(120, 60), 5)

    async def write(self, *, topic, tone, angles, count, avoid, feedback) -> LLMResult[DraftBatch]:
        await self._maybe_fail("write")
        drafts: list[DraftQuote] = []
        if self.inject_bad_draft and not feedback:  # first round of every run
            drafts.append(self._draft("Never give up and always believe in yourself.", angles))
        while len(drafts) < count:
            line = _GOOD_LINES[self._cursor % len(_GOOD_LINES)]
            self._cursor += 1
            drafts.append(self._draft(line, angles))
        return LLMResult(DraftBatch(quotes=drafts[:count]), Usage(400, 300), 8)

    async def review(self, *, topic, tone, quotes) -> LLMResult[ReviewBatch]:
        await self._maybe_fail("review")
        reviews = [
            QuoteReview(
                index=i,
                originality=8,
                clarity=9,
                impact=8 if i % 2 == 0 else 7,
                on_topic=9,
                safe=True,
                feedback="Tighten the second half.",
            )
            for i, _ in enumerate(quotes)
        ]
        return LLMResult(ReviewBatch(reviews=reviews), Usage(300, 150), 6)

    @staticmethod
    def _draft(text: str, angles: list[str]) -> DraftQuote:
        return DraftQuote(
            text=text,
            angle=angles[0] if angles else "general",
            keywords=["mountain", "sunrise"],
            hashtags=["mindset", "growth", "quotes", "dailyquotes"],
            reflection="A reminder that steady effort beats sudden bursts.",
        )
