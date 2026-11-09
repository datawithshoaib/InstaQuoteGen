"use client";

import { motion } from "motion/react";
import { BookOpen, Check, Compass, Feather, Gavel, Loader2, RotateCcw, Sparkle, X } from "lucide-react";
import type { StepEvent } from "@/lib/types";
import { ms } from "@/lib/format";
import { cn } from "@/lib/utils";

const NODES = [
  { id: "plan", title: "Plan", blurb: "Find fresh angles", icon: Compass },
  { id: "write", title: "Write", blurb: "Draft as structured output", icon: Feather },
  { id: "review", title: "Review", blurb: "Guard rails + LLM judge", icon: Gavel },
  { id: "finalize", title: "Finalize", blurb: "Rank, tag, polish", icon: Sparkle },
] as const;

type NodeState = "idle" | "running" | "done" | "error";

function latest(steps: StepEvent[], node: string) {
  const matching = steps.filter((s) => s.node === node);
  return matching[matching.length - 1];
}

export function PipelineGraph({ steps, active }: { steps: StepEvent[]; active: boolean }) {
  const libraryStep = latest(steps, "library");
  const rounds = Math.max(0, ...steps.filter((s) => s.node === "write").map((s) => s.round ?? 0));

  return (
    <div className="glass relative overflow-hidden rounded-2xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">LangGraph pipeline</p>
        {rounds > 1 && (
          <motion.span
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-1 rounded-full bg-violet/15 px-2.5 py-0.5 text-xs text-violet"
          >
            <RotateCcw className="size-3" /> rewrite round {rounds}
          </motion.span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {NODES.map((node, i) => {
          const step = latest(steps, node.id);
          const state = (step?.status ?? "idle") as NodeState;
          const Icon = node.icon;
          return (
            <div key={node.id} className="relative">
              {i > 0 && (
                <div className="absolute top-1/2 -left-3 hidden h-px w-3 overflow-hidden bg-white/10 md:block">
                  <motion.div
                    className="h-full bg-gradient-to-r from-gold to-violet"
                    initial={{ width: 0 }}
                    animate={{ width: state !== "idle" ? "100%" : 0 }}
                    transition={{ duration: 0.4 }}
                  />
                </div>
              )}
              <motion.div
                layout
                className={cn(
                  "relative h-full rounded-xl border p-3.5 transition-colors",
                  state === "idle" && "border-white/8 bg-white/[0.02]",
                  state === "running" && "border-gold/50 bg-gold/[0.07] animate-pulse-ring",
                  state === "done" && "border-success/30 bg-success/[0.06]",
                  state === "error" && "border-destructive/40 bg-destructive/10",
                )}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "grid size-8 place-items-center rounded-lg",
                      state === "idle" ? "bg-white/5 text-muted-foreground" : "bg-white/10 text-foreground",
                    )}
                  >
                    <Icon className="size-4" />
                  </span>
                  <StateIcon state={state} />
                </div>
                <p className="mt-3 text-sm font-medium">
                  {node.title}
                  {step?.round ? <span className="ml-1.5 font-mono text-xs text-muted-foreground">#{step.round}</span> : null}
                </p>
                <p className="mt-0.5 line-clamp-2 min-h-8 text-xs text-muted-foreground">
                  {step?.detail || node.blurb}
                </p>
                <p className="mt-2 font-mono text-[11px] text-muted-foreground/80">
                  {state === "done" || state === "error" ? ms(step?.duration_ms) : state === "running" ? "working…" : " "}
                </p>
              </motion.div>
            </div>
          );
        })}
      </div>

      {libraryStep && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 flex items-center gap-3 rounded-xl border border-warning/30 bg-warning/10 p-3 text-sm"
        >
          <BookOpen className="size-4 shrink-0 text-warning" />
          <span className="flex-1">
            <span className="font-medium">Library fallback</span>{" "}
            <span className="text-muted-foreground">{libraryStep.detail || "Picking from your saved quotes"}</span>
          </span>
          <StateIcon state={libraryStep.status} />
        </motion.div>
      )}

      {!active && steps.length === 0 && (
        <p className="mt-4 text-center text-xs text-muted-foreground">
          Each step lights up live as the backend streams events over SSE.
        </p>
      )}
    </div>
  );
}

function StateIcon({ state }: { state: NodeState }) {
  if (state === "running") return <Loader2 className="size-4 animate-spin text-gold" />;
  if (state === "done") return <Check className="size-4 text-success" />;
  if (state === "error") return <X className="size-4 text-destructive" />;
  return <span className="size-2 rounded-full bg-white/15" />;
}
