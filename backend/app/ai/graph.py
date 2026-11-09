"""The quote-writing pipeline, built with LangGraph.

    START -> plan -> write -> review --(enough good quotes or out of rounds)--> finalize -> END
                       ^         |
                       +---------+  (rewrite with editor feedback)

* plan      LLM proposes fresh angles and a visual mood for the topic.
* write     LLM drafts quotes as structured output, told what to avoid.
* review    Rule-based guard rails first, then an LLM judge scores what is left.
            Rejected drafts turn into feedback for the next round.
* finalize  Keep the best N, tidy hashtags and keywords.

The graph is compiled once. Per-run dependencies (LLM client, tracer, quality
bar) are passed in through LangGraph's runtime context.
"""

import operator
from dataclasses import dataclass
from statistics import mean
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from app.ai.guardrails import check_draft
from app.ai.llm import QuoteLLM
from app.ai.tracing import RunTracer
from app.core.text import clean_tag


class PipelineState(TypedDict):
    topic: str
    tone: str
    count: int
    max_rounds: int
    avoid: list[str]
    angles: list[str]
    visual_mood: list[str]
    round: int
    drafts: list[dict[str, Any]]
    accepted: Annotated[list[dict[str, Any]], operator.add]
    rejected: Annotated[list[dict[str, Any]], operator.add]
    feedback: list[str]
    final: list[dict[str, Any]]


@dataclass
class PipelineContext:
    llm: QuoteLLM
    tracer: RunTracer
    min_score: float


# --------------------------------------------------------------------- nodes


async def plan(state: PipelineState, runtime: Runtime[PipelineContext]) -> dict[str, Any]:
    ctx = runtime.context
    async with ctx.tracer.step("plan", "Planning angles") as step:
        result = await ctx.llm.plan(topic=state["topic"], tone=state["tone"])
        ctx.tracer.record_usage(result.usage)
        angles = [a.strip() for a in result.value.angles if a.strip()][:5] or [state["topic"]]
        mood = [m.strip().lower() for m in result.value.visual_mood if m.strip()][:5]
        step.detail = " · ".join(angles)
    return {"angles": angles, "visual_mood": mood}


async def write(state: PipelineState, runtime: Runtime[PipelineContext]) -> dict[str, Any]:
    ctx = runtime.context
    round_no = state["round"] + 1
    still_needed = state["count"] - len(state["accepted"])
    ask_for = still_needed + 1  # one spare, because some drafts will not survive review

    avoid = (
        state["avoid"][-20:] + [q["text"] for q in state["accepted"]] + [q["text"] for q in state["rejected"]]
    )
    async with ctx.tracer.step("write", "Drafting quotes", round=round_no) as step:
        result = await ctx.llm.write(
            topic=state["topic"],
            tone=state["tone"],
            angles=state["angles"],
            count=ask_for,
            avoid=avoid,
            feedback=state["feedback"],
        )
        ctx.tracer.record_usage(result.usage)
        drafts = [d.model_dump() for d in result.value.quotes][: ask_for + 2]
        step.detail = f"{len(drafts)} drafts"
    return {"drafts": drafts, "round": round_no}


async def review(state: PipelineState, runtime: Runtime[PipelineContext]) -> dict[str, Any]:
    ctx = runtime.context
    round_no = state["round"]
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    async with ctx.tracer.step("review", "Reviewing drafts", round=round_no) as step:
        # 1) Cheap deterministic rails.
        seen = state["avoid"] + [q["text"] for q in state["accepted"]]
        survivors: list[dict[str, Any]] = []
        for draft in state["drafts"]:
            check = check_draft(draft["text"], seen)
            draft = {**draft, "text": check.text}
            if check.passed:
                survivors.append(draft)
                seen.append(check.text)
            else:
                rejected.append({**draft, "reasons": check.reasons, "stage": "rules"})

        # 2) LLM-as-judge on whatever is left.
        if survivors:
            result = await ctx.llm.review(
                topic=state["topic"], tone=state["tone"], quotes=[d["text"] for d in survivors]
            )
            ctx.tracer.record_usage(result.usage)
            reviews = {r.index: r for r in result.value.reviews}
            for i, draft in enumerate(survivors):
                r = reviews.get(i)
                if r is None:
                    rejected.append({**draft, "reasons": ["judge skipped it"], "stage": "judge"})
                    continue
                scores = {
                    "originality": r.originality,
                    "clarity": r.clarity,
                    "impact": r.impact,
                    "on_topic": r.on_topic,
                }
                score = round(mean(scores.values()), 2)
                scored = {**draft, "score": score, "scores": scores, "feedback": r.feedback}
                if not r.safe:
                    rejected.append({**scored, "reasons": ["flagged as unsafe"], "stage": "judge"})
                elif score < ctx.min_score:
                    reason = f"scored {score:.1f}, below the {ctx.min_score:.1f} bar"
                    rejected.append({**scored, "reasons": [reason], "stage": "judge"})
                else:
                    accepted.append(scored)

        labelled = [(q, "accepted") for q in accepted] + [(q, "rejected") for q in rejected]
        for item, status in labelled:
            await ctx.tracer.event(
                "candidate",
                {
                    "round": round_no,
                    "text": item["text"],
                    "status": status,
                    "score": item.get("score"),
                    "scores": item.get("scores"),
                    "reasons": item.get("reasons", []),
                    "stage": item.get("stage"),
                },
            )
        step.detail = f"{len(accepted)} kept, {len(rejected)} rejected"

    feedback = [
        f'"{q["text"]}" was rejected: {"; ".join(q["reasons"])}. {q.get("feedback", "")}'.strip()
        for q in rejected
    ][:6]
    return {"accepted": accepted, "rejected": rejected, "feedback": feedback}


def route_after_review(state: PipelineState) -> Literal["write", "finalize"]:
    if len(state["accepted"]) >= state["count"] or state["round"] >= state["max_rounds"]:
        return "finalize"
    return "write"


async def finalize(state: PipelineState, runtime: Runtime[PipelineContext]) -> dict[str, Any]:
    ctx = runtime.context
    async with ctx.tracer.step("finalize", "Polishing results") as step:
        best = sorted(state["accepted"], key=lambda q: q["score"], reverse=True)[: state["count"]]
        topic_tag = clean_tag(state["topic"])
        final = []
        for q in best:
            tags: list[str] = []
            for tag in [*q.get("hashtags", []), topic_tag, "quotes", "dailyquotes"]:
                t = clean_tag(tag)
                if t and len(t) > 1 and t not in tags:
                    tags.append(t)
            keywords = [k.strip().lower() for k in q.get("keywords", []) if k.strip()]
            final.append(
                {
                    "text": q["text"],
                    "author": None,  # AI-written lines are never attributed to real people
                    "tone": state["tone"],
                    "angle": q.get("angle"),
                    "keywords": (keywords or state["visual_mood"])[:4],
                    "hashtags": tags[:10],
                    "reflection": q.get("reflection"),
                    "score": q["score"],
                    "scores": q["scores"],
                }
            )
        step.detail = f"{len(final)} of {state['count']} requested"
    return {"final": final}


# --------------------------------------------------------------------- graph


def build_graph():
    graph = StateGraph(PipelineState, context_schema=PipelineContext)
    graph.add_node("plan", plan)
    graph.add_node("write", write)
    graph.add_node("review", review)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "write")
    graph.add_edge("write", "review")
    graph.add_conditional_edges("review", route_after_review, ["write", "finalize"])
    graph.add_edge("finalize", END)
    return graph.compile()


quote_pipeline = build_graph()


@dataclass
class PipelineOutput:
    quotes: list[dict[str, Any]]
    rounds: int
    accepted: int
    rejected: int
    visual_mood: list[str]


async def run_pipeline(
    *,
    llm: QuoteLLM,
    tracer: RunTracer,
    topic: str,
    tone: str,
    count: int,
    avoid: list[str],
    min_score: float,
    max_rewrite_rounds: int,
) -> PipelineOutput:
    initial: PipelineState = {
        "topic": topic,
        "tone": tone,
        "count": count,
        "max_rounds": 1 + max_rewrite_rounds,
        "avoid": avoid,
        "angles": [],
        "visual_mood": [],
        "round": 0,
        "drafts": [],
        "accepted": [],
        "rejected": [],
        "feedback": [],
        "final": [],
    }
    state = await quote_pipeline.ainvoke(
        initial, context=PipelineContext(llm=llm, tracer=tracer, min_score=min_score)
    )
    return PipelineOutput(
        quotes=state["final"],
        rounds=state["round"],
        accepted=len(state["accepted"]),
        rejected=len(state["rejected"]),
        visual_mood=state["visual_mood"],
    )
