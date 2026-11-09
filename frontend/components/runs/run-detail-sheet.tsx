"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { compact, ms, studioHref } from "@/lib/format";
import { cn } from "@/lib/utils";

const NODE_COLOR: Record<string, string> = {
  plan: "bg-teal",
  write: "bg-gold",
  review: "bg-violet",
  finalize: "bg-success",
  library: "bg-warning",
};

export function RunDetailSheet({ runId, onClose }: { runId: string | null; onClose: () => void }) {
  const { data: run, isPending } = useQuery({
    queryKey: ["runs", "detail", runId],
    queryFn: () => api.runs.get(runId!),
    enabled: !!runId,
  });

  const total = run ? Math.max(1, ...run.steps.map((s) => s.duration_ms)) : 1;

  return (
    <Sheet open={!!runId} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="font-serif text-2xl italic">{run?.topic ?? "Run"}</SheetTitle>
          <SheetDescription className="font-mono text-xs">{runId}</SheetDescription>
        </SheetHeader>

        {isPending || !run ? (
          <div className="space-y-3 px-4">
            <Skeleton className="h-20" />
            <Skeleton className="h-40" />
          </div>
        ) : (
          <div className="space-y-6 px-4 pb-8">
            <dl className="grid grid-cols-3 gap-3 text-sm">
              {[
                ["Status", run.status],
                ["Model", run.model ?? "library"],
                ["Prompt", run.prompt_version],
                ["Latency", ms(run.latency_ms)],
                ["LLM calls", run.llm_calls],
                ["Tokens", `${compact(run.input_tokens)} in / ${compact(run.output_tokens)} out`],
                ["Rounds", run.rounds || "–"],
                ["Kept", run.accepted_count],
                ["Rejected", run.rejected_count],
              ].map(([k, v]) => (
                <div key={k as string} className="rounded-lg border border-border bg-white/[0.02] p-2.5">
                  <dt className="text-[11px] text-muted-foreground">{k}</dt>
                  <dd className="mt-0.5 truncate font-mono text-xs">{v}</dd>
                </div>
              ))}
            </dl>

            {run.error && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 font-mono text-xs text-destructive">
                {run.error}
              </div>
            )}

            <section>
              <h3 className="mb-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">Trace</h3>
              <ol className="space-y-2">
                {run.steps.map((s, i) => (
                  <li key={i} className="space-y-1">
                    <div className="flex items-baseline justify-between text-sm">
                      <span>
                        {s.label}
                        {s.round ? <span className="ml-1 font-mono text-xs text-muted-foreground">#{s.round}</span> : null}
                      </span>
                      <span className="font-mono text-xs text-muted-foreground">{ms(s.duration_ms)}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-white/5">
                      <div
                        className={cn("h-full rounded-full", NODE_COLOR[s.node] ?? "bg-white/40", s.status === "error" && "bg-destructive")}
                        style={{ width: `${Math.max(2, (s.duration_ms / total) * 100)}%` }}
                      />
                    </div>
                    {s.detail && <p className="text-xs text-muted-foreground">{s.detail}</p>}
                  </li>
                ))}
              </ol>
            </section>

            <section>
              <h3 className="mb-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">Results</h3>
              <ul className="space-y-2">
                {run.results.map((q) => (
                  <li key={q.text} className="rounded-lg border border-border bg-white/[0.02] p-3">
                    <p className="font-serif italic">{q.text}</p>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="font-mono text-xs text-gold">{q.score != null ? `★ ${q.score.toFixed(1)}` : ""}</span>
                      <Button size="xs" variant="ghost" asChild>
                        <Link href={studioHref(q)}>
                          <Palette /> Studio
                        </Link>
                      </Button>
                    </div>
                  </li>
                ))}
                {run.results.length === 0 && <p className="text-sm text-muted-foreground">No quotes came out of this run.</p>}
              </ul>
            </section>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
