"""Tests for the LangGraph pipeline, using the deterministic fake LLM."""

from app.ai.fake_llm import FakeQuoteLLM
from app.ai.graph import run_pipeline
from app.ai.tracing import RunTracer


async def _run(llm, *, count=3, min_score=7.0, rounds=2, avoid=None, emit=None):
    tracer = RunTracer(emit=emit) if emit else RunTracer()
    out = await run_pipeline(
        llm=llm,
        tracer=tracer,
        topic="discipline",
        tone="Bold",
        count=count,
        avoid=avoid or [],
        min_score=min_score,
        max_rewrite_rounds=rounds,
    )
    return out, tracer


async def test_happy_path_returns_requested_count():
    out, tracer = await _run(FakeQuoteLLM(), count=3)
    assert len(out.quotes) == 3
    assert all(q["score"] >= 7.0 for q in out.quotes)
    assert all(q["author"] is None for q in out.quotes), "AI quotes must never be attributed"
    assert all(q["hashtags"] and q["keywords"] for q in out.quotes)
    assert tracer.llm_calls >= 3 and tracer.input_tokens > 0


async def test_cliche_draft_is_rejected_by_rules():
    out, _ = await _run(FakeQuoteLLM(inject_bad_draft=True), count=2)
    assert out.rejected >= 1
    assert all("never give up" not in q["text"].lower() for q in out.quotes)


async def test_rewrite_loop_stops_at_round_limit():
    llm = FakeQuoteLLM()
    out, tracer = await _run(llm, count=2, min_score=9.9, rounds=2)  # nothing can pass
    assert out.quotes == []
    assert out.rounds == 3  # first attempt + 2 rewrites
    assert llm.calls.count("write") == 3
    assert [s.node for s in tracer.steps].count("review") == 3


async def test_results_sorted_by_score_and_deduped_against_library():
    library = ["The quiet work you do at dawn becomes the loud result everyone notices later."]
    out, _ = await _run(FakeQuoteLLM(), count=3, avoid=library)
    texts = [q["text"] for q in out.quotes]
    assert library[0] not in texts
    scores = [q["score"] for q in out.quotes]
    assert scores == sorted(scores, reverse=True)


async def test_emits_step_and_candidate_events():
    events: list[tuple[str, dict]] = []

    async def emit(name, data):
        events.append((name, data))

    await _run(FakeQuoteLLM(), count=2, emit=emit)
    names = {n for n, _ in events}
    assert {"step", "candidate"} <= names
    nodes = [d["node"] for n, d in events if n == "step" and d["status"] == "done"]
    assert nodes[0] == "plan" and nodes[-1] == "finalize"
