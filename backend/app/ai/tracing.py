"""Lightweight run tracing.

Every pipeline step is timed and summarised. The same events feed two
places: the live SSE stream the UI shows while a run is in progress, and the
GenerationRun row we keep afterwards for debugging and analytics.
"""

import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from app.ai.llm import Usage

Emit = Callable[[str, dict[str, Any]], Awaitable[None]]


async def _noop(_: str, __: dict[str, Any]) -> None:
    return None


@dataclass
class Step:
    node: str
    label: str
    round: int | None = None
    status: str = "running"
    detail: str = ""
    duration_ms: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "node": self.node,
            "label": self.label,
            "round": self.round,
            "status": self.status,
            "detail": self.detail,
            "duration_ms": self.duration_ms,
        }


@dataclass
class RunTracer:
    emit: Emit = _noop
    steps: list[Step] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0

    def record_usage(self, usage: Usage) -> None:
        self.llm_calls += 1
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens

    async def event(self, name: str, data: dict[str, Any]) -> None:
        await self.emit(name, data)

    @asynccontextmanager
    async def step(self, node: str, label: str, round: int | None = None) -> AsyncIterator[Step]:
        step = Step(node=node, label=label, round=round)
        self.steps.append(step)
        await self.emit("step", step.as_dict())
        started = time.perf_counter()
        try:
            yield step
            step.status = "done"
        except Exception as exc:
            step.status = "error"
            step.detail = step.detail or str(exc)
            raise
        finally:
            step.duration_ms = int((time.perf_counter() - started) * 1000)
            await self.emit("step", step.as_dict())
