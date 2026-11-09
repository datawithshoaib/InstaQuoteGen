"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Activity, CheckCircle2, Coins, Gauge, Star, Timer } from "lucide-react";
import { RunDetailSheet } from "@/components/runs/run-detail-sheet";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSystem } from "@/hooks/use-system";
import { api } from "@/lib/api";
import { compact, ms, pct, timeAgo } from "@/lib/format";
import type { RunSummary } from "@/lib/types";
import { cn } from "@/lib/utils";

export const STATUS_STYLE: Record<RunSummary["status"], string> = {
  success: "bg-success/15 text-success",
  partial: "bg-warning/15 text-warning",
  fallback: "bg-warning/15 text-warning",
  error: "bg-destructive/15 text-destructive",
};

export function RunsView() {
  const [selected, setSelected] = useState<string | null>(null);
  const { data: system } = useSystem();
  const stats = useQuery({ queryKey: ["runs", "stats"], queryFn: api.runs.stats });
  const runs = useQuery({ queryKey: ["runs", "list"], queryFn: () => api.runs.list({ limit: 50 }) });

  const s = stats.data;
  const successRate = s && s.total_runs ? (s.by_status.success ?? 0) / s.total_runs : null;
  const tiles = [
    { icon: Activity, label: "Runs", value: compact(s?.total_runs) },
    { icon: CheckCircle2, label: "Success rate", value: pct(successRate) },
    { icon: Star, label: "Avg judge score", value: s?.avg_score?.toFixed(2) ?? "–" },
    { icon: Gauge, label: "Draft acceptance", value: pct(s?.acceptance_rate) },
    { icon: Timer, label: "Avg latency", value: ms(s?.avg_latency_ms) },
    { icon: Coins, label: "Tokens used", value: compact(s ? s.total_input_tokens + s.total_output_tokens : null) },
  ];

  return (
    <>
      <PageHeader
        eyebrow="Observability"
        title="What the AI actually did"
        description="Every generation is traced: each step, its timing, token use, judge scores and why drafts were rejected. This is how you tell whether a prompt change made things better or worse."
        actions={
          system && (
            <span className="rounded-full border border-border bg-white/[0.03] px-3 py-1.5 font-mono text-xs text-muted-foreground">
              prompt {system.prompt_version} · bar {system.min_quality_score}/10
            </span>
          )
        }
      />

      <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {tiles.map(({ icon: Icon, label, value }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass rounded-2xl p-4"
          >
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Icon className="size-3.5" /> {label}
            </p>
            {stats.isPending ? (
              <Skeleton className="mt-2 h-8 w-16" />
            ) : (
              <p className="mt-1.5 font-serif text-3xl italic">{value}</p>
            )}
          </motion.div>
        ))}
      </div>

      {runs.isPending ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      ) : runs.isError ? (
        <EmptyState icon={Activity} title="Couldn't load runs" description={runs.error.message} />
      ) : runs.data.items.length === 0 ? (
        <EmptyState
          icon={Activity}
          title="No runs yet"
          description="Run the generator once and its full trace shows up here."
          action={
            <Button asChild>
              <Link href="/generate">Generate quotes</Link>
            </Button>
          }
        />
      ) : (
        <div className="glass overflow-hidden rounded-2xl">
          <div className="hidden grid-cols-[minmax(0,2fr)_100px_90px_80px_80px_90px_90px] gap-3 border-b border-border px-5 py-3 text-xs text-muted-foreground md:grid">
            <span>Topic</span>
            <span>Status</span>
            <span>Source</span>
            <span className="text-right">Rounds</span>
            <span className="text-right">Score</span>
            <span className="text-right">Latency</span>
            <span className="text-right">When</span>
          </div>
          <ul>
            {runs.data.items.map((run) => (
              <li key={run.id}>
                <button
                  type="button"
                  onClick={() => setSelected(run.id)}
                  className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-border/60 px-5 py-3.5 text-left text-sm transition last:border-0 hover:bg-white/[0.03] md:grid-cols-[minmax(0,2fr)_100px_90px_80px_80px_90px_90px]"
                >
                  <span className="min-w-0">
                    <span className="block truncate font-medium">{run.topic}</span>
                    <span className="text-xs text-muted-foreground">
                      {run.tone} · {run.requested_count} requested
                    </span>
                  </span>
                  <span>
                    <span className={cn("rounded-full px-2 py-0.5 text-xs capitalize", STATUS_STYLE[run.status])}>
                      {run.status}
                    </span>
                  </span>
                  <span className="hidden text-muted-foreground md:block">{run.source}</span>
                  <span className="hidden text-right font-mono md:block">{run.rounds || "–"}</span>
                  <span className="hidden text-right font-mono md:block">{run.avg_score?.toFixed(1) ?? "–"}</span>
                  <span className="hidden text-right font-mono md:block">{ms(run.latency_ms)}</span>
                  <span className="hidden text-right text-xs text-muted-foreground md:block">{timeAgo(run.created_at)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <RunDetailSheet runId={selected} onClose={() => setSelected(null)} />
    </>
  );
}
