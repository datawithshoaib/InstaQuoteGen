"use client";

import { useState } from "react";
import { Loader2, Sparkles, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { GenerationRequest, Tone } from "@/lib/types";

const TONES: Tone[] = ["Inspirational", "Stoic", "Bold", "Poetic", "Calm", "Playful", "Melancholic", "Witty"];
const IDEAS = ["discipline", "starting over", "rest & burnout", "first love", "Monday mornings", "creative block"];

export function GenerateForm({
  running,
  onSubmit,
  onCancel,
  initialTopic = "",
}: {
  running: boolean;
  onSubmit: (req: GenerationRequest) => void;
  onCancel: () => void;
  initialTopic?: string;
}) {
  const [topic, setTopic] = useState(initialTopic);
  const [tone, setTone] = useState<Tone>("Inspirational");
  const [count, setCount] = useState(3);

  return (
    <form
      className="glass space-y-6 rounded-2xl p-5 sm:p-6"
      onSubmit={(e) => {
        e.preventDefault();
        if (topic.trim().length >= 2) onSubmit({ topic: topic.trim(), tone, count });
      }}
    >
      <div className="space-y-2">
        <Label htmlFor="topic">What should the quotes be about?</Label>
        <Input
          id="topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. learning to rest without guilt"
          maxLength={80}
          className="h-11 text-base"
          autoFocus
        />
        <div className="flex flex-wrap gap-1.5 pt-1">
          {IDEAS.map((idea) => (
            <button
              key={idea}
              type="button"
              onClick={() => setTopic(idea)}
              className="rounded-full border border-border bg-white/[0.03] px-2.5 py-1 text-xs text-muted-foreground transition hover:border-gold/40 hover:text-foreground"
            >
              {idea}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Tone</Label>
        <ToggleGroup
          type="single"
          value={tone}
          onValueChange={(v) => v && setTone(v as Tone)}
          className="flex w-full flex-wrap justify-start gap-1.5"
          spacing={1}
        >
          {TONES.map((t) => (
            <ToggleGroupItem
              key={t}
              value={t}
              className="rounded-full border border-border px-3 text-xs data-[state=on]:border-gold/50 data-[state=on]:bg-gold/15 data-[state=on]:text-gold"
            >
              {t}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>How many quotes</Label>
          <span className="font-mono text-sm text-gold">{count}</span>
        </div>
        <Slider min={1} max={6} step={1} value={[count]} onValueChange={([v]) => setCount(v)} />
      </div>

      {running ? (
        <Button type="button" variant="outline" size="lg" className="h-11 w-full" onClick={onCancel}>
          <Square className="fill-current" /> Stop
        </Button>
      ) : (
        <Button
          type="submit"
          size="lg"
          disabled={topic.trim().length < 2}
          className="h-11 w-full bg-gradient-to-r from-gold to-[oklch(0.78_0.14_50)] text-base font-semibold shadow-[0_10px_40px_-10px] shadow-gold/60 hover:opacity-95"
        >
          {running ? <Loader2 className="animate-spin" /> : <Sparkles />} Write quotes
        </Button>
      )}
    </form>
  );
}
