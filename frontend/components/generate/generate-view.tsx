"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { AlertTriangle, Coins, Cpu, Feather, Gauge, Repeat, Timer } from "lucide-react";
import { toast } from "sonner";
import { CandidateFeed } from "@/components/generate/candidate-feed";
import { GenerateForm } from "@/components/generate/generate-form";
import { PipelineGraph } from "@/components/generate/pipeline-graph";
import { QuoteResultCard } from "@/components/generate/quote-result-card";
import { PostDialog } from "@/components/post/post-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { useGenerationStream } from "@/hooks/use-generation-stream";
import { useCreatePost, useSaveQuote } from "@/hooks/use-mutations";
import { useSystem } from "@/hooks/use-system";
import { compact, ms } from "@/lib/format";
import type { GeneratedQuote, GenerationResponse, Post } from "@/lib/types";
import { cn } from "@/lib/utils";

export function GenerateView() {
  const params = useSearchParams();
  const stream = useGenerationStream();
  const { data: system } = useSystem();
  const save = useSaveQuote();
  const createPost = useCreatePost();
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [making, setMaking] = useState<string | null>(null);
  const [post, setPost] = useState<Post | null>(null);

  const running = stream.status === "running";
  const result = stream.result;

  function saveQuote(q: GeneratedQuote) {
    save.mutate(
      {
        text: q.text,
        tone: q.tone,
        keywords: q.keywords,
        hashtags: q.hashtags,
        reflection: q.reflection,
        source: "ai",
        quality_score: q.score,
        run_id: result?.run_id,
      },
      { onSuccess: () => setSaved((s) => new Set(s).add(q.text)) },
    );
  }

  function makePost(q: GeneratedQuote) {
    setMaking(q.text);
    createPost.mutate(
      { quote: { text: q.text, author: q.author, keywords: q.keywords, hashtags: q.hashtags, reflection: q.reflection } },
      {
        onSuccess: (p) => {
          setPost(p);
          toast.success("Post rendered and added to your gallery");
        },
        onSettled: () => setMaking(null),
      },
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Generate"
        title={
          <>
            Quotes that earn the <span className="text-gradient">stop-scroll</span>
          </>
        }
        description="A small LangGraph pipeline plans angles, drafts quotes, then a rule checker and an LLM judge throw out the weak ones and send notes back for a rewrite. You watch it happen live."
      />

      {system && !system.llm.enabled && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" />
          <p>
            <span className="font-medium">Library mode.</span>{" "}
            <span className="text-muted-foreground">
              No <code className="font-mono text-foreground">GROQ_API_KEY</code> in{" "}
              <code className="font-mono text-foreground">backend/.env</code>, so results come from your saved quotes.
              Add a free Groq key to switch on the full AI pipeline.
            </span>
          </p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
        <div className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <GenerateForm
            running={running}
            onSubmit={stream.start}
            onCancel={stream.cancel}
            initialTopic={params.get("topic") ?? ""}
          />
          {result && <RunMeta result={result} />}
        </div>

        <div className="min-w-0 space-y-4">
          <PipelineGraph steps={stream.steps} active={running} />

          {stream.error && (
            <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
              {stream.error}
            </div>
          )}

          {result?.note && (
            <div className="rounded-xl border border-border bg-white/[0.03] p-4 text-sm text-muted-foreground">
              {result.note}
            </div>
          )}

          <AnimatePresence mode="popLayout">
            {result && result.quotes.length > 0 ? (
              <motion.div key={result.run_id} className="grid gap-4 xl:grid-cols-2">
                {result.quotes.map((q, i) => (
                  <QuoteResultCard
                    key={q.text}
                    quote={q}
                    index={i}
                    saved={saved.has(q.text)}
                    saving={save.isPending && save.variables?.text === q.text}
                    making={making === q.text}
                    onSave={() => saveQuote(q)}
                    onMakePost={() => makePost(q)}
                  />
                ))}
              </motion.div>
            ) : running ? (
              <motion.div key="loading" className="grid gap-4 xl:grid-cols-2" exit={{ opacity: 0 }}>
                {[0, 1].map((i) => (
                  <div key={i} className="glass h-56 overflow-hidden rounded-2xl">
                    <div className="shimmer size-full" />
                  </div>
                ))}
              </motion.div>
            ) : (
              !result && (
                <motion.div
                  key="empty"
                  exit={{ opacity: 0 }}
                  className="glass flex flex-col items-center gap-3 rounded-2xl px-6 py-14 text-center"
                >
                  <Feather className="size-6 text-gold" />
                  <p className="font-serif text-2xl italic">Give it a topic.</p>
                  <p className="max-w-md text-sm text-muted-foreground">
                    Something specific works best. &ldquo;Discipline&rdquo; is fine,
                    &ldquo;getting up early when nobody is watching&rdquo; is better.
                  </p>
                </motion.div>
              )
            )}
          </AnimatePresence>

          <CandidateFeed candidates={stream.candidates} />
        </div>
      </div>

      <PostDialog post={post} open={!!post} onOpenChange={(o) => !o && setPost(null)} />
    </>
  );
}

function RunMeta({ result }: { result: GenerationResponse }) {
  const items = [
    { icon: Cpu, label: "Model", value: result.model ?? "library" },
    { icon: Timer, label: "Latency", value: ms(result.latency_ms) },
    { icon: Repeat, label: "Rounds", value: String(result.rounds || "–") },
    { icon: Coins, label: "Tokens", value: compact(result.usage.input_tokens + result.usage.output_tokens) },
    { icon: Gauge, label: "LLM calls", value: String(result.usage.llm_calls) },
  ];
  const tone = {
    success: "bg-success/15 text-success",
    partial: "bg-warning/15 text-warning",
    fallback: "bg-warning/15 text-warning",
    error: "bg-destructive/15 text-destructive",
  }[result.status];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl p-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">This run</p>
        <span className={cn("rounded-full px-2 py-0.5 text-xs capitalize", tone)}>{result.status}</span>
      </div>
      <dl className="grid grid-cols-2 gap-3 text-sm">
        {items.map(({ icon: Icon, label, value }) => (
          <div key={label}>
            <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Icon className="size-3" /> {label}
            </dt>
            <dd className="mt-0.5 truncate font-mono text-[13px]">{value}</dd>
          </div>
        ))}
        <div>
          <dt className="text-xs text-muted-foreground">Prompt</dt>
          <dd className="mt-0.5 truncate font-mono text-[13px]">{result.prompt_version}</dd>
        </div>
      </dl>
    </motion.div>
  );
}
