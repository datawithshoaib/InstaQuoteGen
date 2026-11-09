"use client";

import { AnimatePresence, motion } from "motion/react";
import { CheckCircle2, XCircle } from "lucide-react";
import type { CandidateEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Every draft the reviewer looked at, accepted or not. This is the "why" behind the results. */
export function CandidateFeed({ candidates }: { candidates: CandidateEvent[] }) {
  if (candidates.length === 0) return null;
  const accepted = candidates.filter((c) => c.status === "accepted").length;

  return (
    <div className="glass rounded-2xl p-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">Reviewer log</p>
        <p className="text-xs text-muted-foreground">
          <span className="text-success">{accepted} kept</span> ·{" "}
          <span className="text-destructive">{candidates.length - accepted} rejected</span>
        </p>
      </div>
      <ul className="max-h-80 space-y-2 overflow-y-auto pr-1">
        <AnimatePresence initial={false}>
          {candidates.map((c, i) => (
            <motion.li
              key={`${c.round}-${i}`}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: (i % 6) * 0.06 }}
              className={cn(
                "flex gap-3 rounded-lg border p-3 text-sm",
                c.status === "accepted" ? "border-success/20 bg-success/[0.04]" : "border-white/6 bg-white/[0.02]",
              )}
            >
              {c.status === "accepted" ? (
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
              ) : (
                <XCircle className="mt-0.5 size-4 shrink-0 text-destructive/80" />
              )}
              <div className="min-w-0 flex-1">
                <p className={cn("font-serif italic", c.status === "rejected" && "text-muted-foreground line-through decoration-destructive/40")}>
                  {c.text}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  round {c.round}
                  {c.stage && <> · {c.stage === "rules" ? "rule check" : "LLM judge"}</>}
                  {c.reasons.length > 0 && <> · {c.reasons.join("; ")}</>}
                </p>
              </div>
              {c.score != null && (
                <span
                  className={cn(
                    "h-fit rounded-md px-1.5 py-0.5 font-mono text-xs",
                    c.status === "accepted" ? "bg-success/15 text-success" : "bg-white/5 text-muted-foreground",
                  )}
                >
                  {c.score.toFixed(1)}
                </span>
              )}
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </div>
  );
}
