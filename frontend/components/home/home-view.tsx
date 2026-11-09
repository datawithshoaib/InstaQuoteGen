/* eslint-disable @next/next/no-img-element -- rendered posts are served by the API */
"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { ArrowRight, Compass, Feather, Gavel, ImageIcon, ShieldCheck, Sparkles } from "lucide-react";
import { PostPreview } from "@/components/post/post-preview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSystem } from "@/hooks/use-system";
import { api, mediaUrl } from "@/lib/api";
import type { PostStyle } from "@/lib/types";

const base: PostStyle = {
  aspect_ratio: "portrait",
  font_size: 66,
  text_color: "#FFFFFF",
  accent_color: "#F5C26B",
  align: "center",
  overlay_opacity: 0.1,
  watermark: "@instaquote.studio",
  show_author: false,
  show_logo: false,
  show_quote_mark: true,
};

const HERO_CARDS = [
  { text: "Rest is part of the climb, not a detour from it.", palette: "aurora", tilt: -9, x: "-92%", y: 46, delay: 0 },
  { text: "What you repeat in private is what you become in public.", palette: "ember", tilt: 0, x: "-50%", y: 0, delay: 0.15 },
  { text: "Calm is not the absence of storms, it is knowing where your anchor is.", palette: "ocean", tilt: 9, x: "-8%", y: 46, delay: 0.3 },
];

const STEPS = [
  { icon: Compass, title: "Plan", body: "The model proposes a few specific angles on your topic, so every quote doesn't say the same thing." },
  { icon: Feather, title: "Write", body: "Drafts come back as structured JSON validated by Pydantic. No regex scraping of free text." },
  { icon: Gavel, title: "Review", body: "Cheap rule checks first (length, clichés, near-duplicates), then an LLM judge scores what's left. Weak drafts go back with notes." },
  { icon: ImageIcon, title: "Render", body: "A matching Unsplash photo (or a generated gradient), balanced typography and a ready-to-paste caption." },
];

export function HomeView() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const { data: system } = useSystem();
  const posts = useQuery({ queryKey: ["posts", "recent"], queryFn: () => api.posts.list({ limit: 8 }) });

  return (
    <div className="space-y-28">
      {/* ------------------------------------------------------------ hero */}
      <section className="grid items-center gap-12 pt-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)] lg:pt-12">
        <div>
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-5 inline-flex items-center gap-2 rounded-full border border-gold/25 bg-gold/10 px-3 py-1 text-xs text-gold"
          >
            <Sparkles className="size-3.5" /> LangGraph · FastAPI · Next.js
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05, duration: 0.6 }}
            className="font-serif text-5xl leading-[1.05] tracking-tight text-balance italic sm:text-6xl lg:text-7xl"
          >
            Words worth <span className="text-gradient">stopping the scroll</span> for.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12, duration: 0.6 }}
            className="mt-6 max-w-xl text-lg text-pretty text-muted-foreground"
          >
            Give it a topic. An AI pipeline writes quotes, a strict reviewer throws out the clichés,
            and the studio turns the best one into a post you can publish.
          </motion.p>

          <motion.form
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            onSubmit={(e) => {
              e.preventDefault();
              router.push(`/generate${topic.trim() ? `?topic=${encodeURIComponent(topic.trim())}` : ""}`);
            }}
            className="glass mt-8 flex max-w-xl items-center gap-2 rounded-2xl p-2"
          >
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Try “starting over at 30”"
              className="h-11 border-0 bg-transparent text-base shadow-none focus-visible:ring-0 dark:bg-transparent"
              aria-label="Topic"
            />
            <Button type="submit" size="lg" className="h-11 shrink-0 bg-gradient-to-r from-gold to-[oklch(0.78_0.14_50)] px-5 font-semibold">
              Generate <ArrowRight />
            </Button>
          </motion.form>

          <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
            <span>
              <span className="font-mono text-foreground">{system?.counts.quotes ?? "–"}</span> quotes in library
            </span>
            <span>
              <span className="font-mono text-foreground">{system?.counts.posts ?? "–"}</span> posts made
            </span>
            <span>
              <span className="font-mono text-foreground">{system?.counts.runs ?? "–"}</span> traced runs
            </span>
          </div>
        </div>

        <div className="relative mx-auto h-[420px] w-full max-w-[520px] sm:h-[480px]">
          {HERO_CARDS.map((card, i) => (
            <motion.div
              key={card.text}
              initial={{ opacity: 0, y: 40, rotate: card.tilt }}
              animate={{ opacity: 1, y: card.y, rotate: card.tilt }}
              transition={{ delay: 0.25 + card.delay, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="absolute top-0 left-1/2 w-[50%] sm:w-[58%]"
              style={{ translate: card.x, zIndex: i === 1 ? 3 : 1 }}
            >
              <div className="animate-float" style={{ animationDelay: `${i * -3}s` }}>
                <PostPreview
                  text={card.text}
                  style={base}
                  palette={card.palette}
                  className="rounded-2xl shadow-[0_30px_80px_-20px_rgba(0,0,0,0.8)] ring-1 ring-white/10"
                />
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------- how it works */}
      <section>
        <div className="mb-10 max-w-2xl">
          <p className="mb-2 text-xs font-medium tracking-[0.2em] text-gold/90 uppercase">How it works</p>
          <h2 className="font-serif text-4xl italic">Not one prompt. A small, honest pipeline.</h2>
          <p className="mt-3 text-muted-foreground">
            Each step is a node in a LangGraph graph. Every run is traced, so you can see what was rejected and why.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(({ icon: Icon, title, body }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ delay: i * 0.08 }}
              className="glass relative overflow-hidden rounded-2xl p-6"
            >
              <span className="absolute top-4 right-5 font-serif text-5xl text-white/5 italic">0{i + 1}</span>
              <span className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-gold/25 to-violet/25 ring-1 ring-white/10">
                <Icon className="size-5" />
              </span>
              <h3 className="mt-5 font-serif text-2xl italic">{title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{body}</p>
            </motion.div>
          ))}
        </div>
        <div className="mt-4 flex items-center gap-3 rounded-2xl border border-border bg-white/[0.02] p-4 text-sm text-muted-foreground">
          <ShieldCheck className="size-4 shrink-0 text-success" />
          Inputs are checked for prompt injection, AI quotes are never attributed to real people, and if the model is down
          you still get quotes from your library.
        </div>
      </section>

      {/* ----------------------------------------------------- recent posts */}
      {posts.data && posts.data.items.length > 0 && (
        <section>
          <div className="mb-6 flex items-end justify-between">
            <h2 className="font-serif text-4xl italic">Recently made</h2>
            <Button variant="ghost" asChild>
              <Link href="/gallery">
                Gallery <ArrowRight />
              </Link>
            </Button>
          </div>
          <div className="-mx-4 flex snap-x gap-4 overflow-x-auto px-4 pb-4">
            {posts.data.items.map((p) => (
              <Link key={p.id} href="/gallery" className="w-56 shrink-0 snap-start">
                <img
                  src={mediaUrl(p.url)}
                  alt={p.quote_text}
                  loading="lazy"
                  className="w-full rounded-xl ring-1 ring-white/10 transition hover:ring-gold/50"
                  style={{ aspectRatio: `${p.width} / ${p.height}` }}
                />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
