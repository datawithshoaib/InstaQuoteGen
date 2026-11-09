from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.api.deps import GenerationServiceDep, SessionDep
from app.core.errors import NotFoundError
from app.repositories.runs import RunRepository
from app.schemas import Page
from app.schemas.generation import (
    GenerationRequest,
    GenerationResponse,
    RunDetail,
    RunStats,
    RunSummary,
)

router = APIRouter(tags=["generation"])


@router.post("/generations", response_model=GenerationResponse)
async def generate(payload: GenerationRequest, service: GenerationServiceDep):
    """Run the full pipeline and return the result in one response."""
    return await service.generate(payload)


@router.post("/generations/stream", response_class=EventSourceResponse)
async def generate_stream(
    payload: GenerationRequest, service: GenerationServiceDep
) -> AsyncIterable[ServerSentEvent]:
    """Same pipeline, streamed as Server-Sent Events.

    Events: `run` (metadata), `step` (node started / finished), `candidate`
    (a draft was accepted or rejected, with scores), then `result` or `error`.
    """
    async for name, data in service.stream(payload):
        yield ServerSentEvent(event=name, data=data)


@router.get("/runs", response_model=Page[RunSummary])
def list_runs(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = RunRepository(session).page(limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/runs/stats", response_model=RunStats)
def run_stats(session: SessionDep):
    return RunRepository(session).stats()


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str, session: SessionDep):
    run = RunRepository(session).get(run_id)
    if run is None:
        raise NotFoundError("Run not found.")
    return run
