"""Offline evaluation of the quote pipeline.

    uv run python -m evals.run            # real model (needs GROQ_API_KEY)
    uv run python -m evals.run --fake     # deterministic fake model, free

Runs every case in evals/dataset.jsonl through the same LangGraph pipeline
the API uses, then scores the output. Results are printed and written to
evals/reports/ as Markdown so runs can be compared across prompt versions.

Metrics
  success_rate       share of cases that returned the requested number of quotes
  avg_judge_score    mean LLM-judge score of the returned quotes (0-10)
  acceptance_rate    accepted drafts / all reviewed drafts (how often the writer hits the bar)
  rule_pass_rate     returned quotes that still pass every deterministic guard rail (should be 1.0)
  diversity          1 - mean pairwise similarity inside a batch (higher = less repetitive)
  avg_rounds         writer attempts per case (1 = first try was good enough)
  avg_latency_ms     wall-clock time per case
  tokens_per_quote   (input + output tokens) / returned quotes
"""

import argparse
import asyncio
import json
import time
from datetime import datetime
from itertools import combinations
from pathlib import Path
from statistics import mean

from app.ai.fake_llm import FakeQuoteLLM
from app.ai.graph import run_pipeline
from app.ai.guardrails import check_draft, similarity
from app.ai.llm import build_llm
from app.ai.prompts import PROMPT_VERSION
from app.ai.tracing import RunTracer
from app.core.config import get_settings

HERE = Path(__file__).parent


async def evaluate_case(llm, case: dict, settings) -> dict:
    tracer = RunTracer()
    started = time.perf_counter()
    error = None
    try:
        out = await run_pipeline(
            llm=llm,
            tracer=tracer,
            topic=case["topic"],
            tone=case["tone"],
            count=case["count"],
            avoid=[],
            min_score=settings.min_quality_score,
            max_rewrite_rounds=settings.max_rewrite_rounds,
        )
        quotes, rounds, accepted, rejected = out.quotes, out.rounds, out.accepted, out.rejected
    except Exception as exc:
        quotes, rounds, accepted, rejected, error = [], 0, 0, 0, str(exc)
    latency = int((time.perf_counter() - started) * 1000)

    texts = [q["text"] for q in quotes]
    pairs = list(combinations(texts, 2))
    return {
        **case,
        "returned": len(quotes),
        "success": len(quotes) >= case["count"],
        "scores": [q["score"] for q in quotes],
        "rule_pass": [check_draft(t, [o for o in texts if o != t]).passed for t in texts],
        "diversity": 1 - mean(similarity(a, b) for a, b in pairs) if pairs else None,
        "accepted": accepted,
        "rejected": rejected,
        "rounds": rounds,
        "latency_ms": latency,
        "tokens": tracer.input_tokens + tracer.output_tokens,
        "quotes": texts,
        "error": error,
    }


def summarise(results: list[dict]) -> dict:
    def avg(values):
        values = [v for v in values if v is not None]
        return round(mean(values), 3) if values else None

    reviewed = sum(r["accepted"] + r["rejected"] for r in results)
    returned = sum(r["returned"] for r in results)
    rule_checks = [p for r in results for p in r["rule_pass"]]
    return {
        "cases": len(results),
        "success_rate": avg([1.0 if r["success"] else 0.0 for r in results]),
        "avg_judge_score": avg([s for r in results for s in r["scores"]]),
        "acceptance_rate": round(sum(r["accepted"] for r in results) / reviewed, 3) if reviewed else None,
        "rule_pass_rate": avg([1.0 if p else 0.0 for p in rule_checks]),
        "diversity": avg([r["diversity"] for r in results]),
        "avg_rounds": avg([r["rounds"] for r in results]),
        "avg_latency_ms": avg([r["latency_ms"] for r in results]),
        "tokens_per_quote": round(sum(r["tokens"] for r in results) / returned, 1) if returned else None,
    }


def write_report(summary: dict, results: list[dict], model: str) -> Path:
    reports = HERE / "reports"
    reports.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = reports / f"{stamp}-{model.replace('/', '_')}.md"
    lines = [
        f"# Eval report: {model}",
        "",
        f"- Prompt version: `{PROMPT_VERSION}`",
        f"- Date: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in summary.items()],
        "",
        "## Cases",
        "",
    ]
    for r in results:
        status = "ok" if r["success"] else ("error: " + r["error"] if r["error"] else "short")
        lines += [
            f"### {r['topic']} ({r['tone']}) - {status}",
            "",
            f"rounds {r['rounds']} · {r['latency_ms']} ms · {r['tokens']} tokens · scores {r['scores']}",
            "",
            *[f"> {q}" for q in r["quotes"]],
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--fake", action="store_true", help="use the deterministic fake LLM")
    parser.add_argument("--limit", type=int, default=None, help="only run the first N cases")
    args = parser.parse_args()

    settings = get_settings()
    llm = FakeQuoteLLM() if args.fake else build_llm(settings)
    if llm is None:
        raise SystemExit("No GROQ_API_KEY configured. Set one in backend/.env or run with --fake.")

    cases = [json.loads(line) for line in (HERE / "dataset.jsonl").read_text().splitlines() if line.strip()]
    cases = cases[: args.limit] if args.limit else cases

    results = []
    for case in cases:
        result = await evaluate_case(llm, case, settings)
        flag = "ok " if result["success"] else "!! "
        print(f"{flag}{case['topic']:<30} scores={result['scores']} rounds={result['rounds']}")
        results.append(result)

    summary = summarise(results)
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nReport written to {write_report(summary, results, llm.model_name)}")


if __name__ == "__main__":
    asyncio.run(main())
