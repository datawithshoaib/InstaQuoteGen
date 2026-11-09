"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { BookmarkPlus, Check, ImagePlus, Loader2, Palette } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { studioHref } from "@/lib/format";
import type { GeneratedQuote } from "@/lib/types";

const LABELS: Record<string, string> = {
  originality: "Original",
  clarity: "Clear",
  impact: "Impact",
  on_topic: "On topic",
};

export function QuoteResultCard({
  quote,
  index,
  saved,
  saving,
  making,
  onSave,
  onMakePost,
}: {
  quote: GeneratedQuote;
  index: number;
  saved: boolean;
  saving: boolean;
  making: boolean;
  onSave: () => void;
  onMakePost: () => void;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 24, filter: "blur(6px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      transition={{ delay: index * 0.12, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="glass group relative flex flex-col overflow-hidden rounded-2xl p-6"
    >
      <span className="pointer-events-none absolute -top-6 -left-1 font-serif text-[9rem] leading-none text-gold/15 italic">
        &ldquo;
      </span>

      <p className="relative font-serif text-xl leading-snug text-balance italic sm:text-2xl">{quote.text}</p>
      {quote.author && <p className="mt-2 text-sm text-gold">— {quote.author}</p>}
      {quote.reflection && <p className="mt-3 text-sm text-muted-foreground">{quote.reflection}</p>}

      {quote.scores && (
        <div className="mt-5 grid grid-cols-4 gap-2">
          {Object.entries(quote.scores).map(([k, v]) => (
            <div key={k}>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/8">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-gold to-violet"
                  initial={{ width: 0 }}
                  animate={{ width: `${v * 10}%` }}
                  transition={{ delay: 0.3 + index * 0.12, duration: 0.8 }}
                />
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {LABELS[k] ?? k} <span className="font-mono text-foreground/80">{v}</span>
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-1.5">
        {quote.score != null && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge className="bg-gold/15 font-mono text-gold">★ {quote.score.toFixed(1)}</Badge>
            </TooltipTrigger>
            <TooltipContent>Average LLM-judge score out of 10</TooltipContent>
          </Tooltip>
        )}
        {quote.angle && <Badge variant="secondary">{quote.angle}</Badge>}
        {quote.keywords.slice(0, 3).map((k) => (
          <Badge key={k} variant="outline" className="text-muted-foreground">
            {k}
          </Badge>
        ))}
      </div>

      <div className="mt-5 flex flex-wrap gap-2 border-t border-border pt-4">
        <Button size="sm" onClick={onMakePost} disabled={making}>
          {making ? <Loader2 className="animate-spin" /> : <ImagePlus />} Make post
        </Button>
        <Button size="sm" variant="outline" asChild>
          <Link href={studioHref(quote)}>
            <Palette /> Open in studio
          </Link>
        </Button>
        {quote.library_id == null && (
          <Button size="sm" variant="ghost" onClick={onSave} disabled={saved || saving}>
            {saved ? <Check className="text-success" /> : saving ? <Loader2 className="animate-spin" /> : <BookmarkPlus />}
            {saved ? "Saved" : "Save"}
          </Button>
        )}
      </div>
    </motion.article>
  );
}
