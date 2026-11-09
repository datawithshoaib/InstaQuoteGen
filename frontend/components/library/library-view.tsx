"use client";

import { useState } from "react";
import Link from "next/link";
import { useInfiniteQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { BookOpen, Loader2, Palette, Search, Sparkles, Trash2 } from "lucide-react";
import { AddQuoteDialog } from "@/components/library/add-quote-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDebounced } from "@/hooks/use-debounced";
import { useDeleteQuote } from "@/hooks/use-mutations";
import { api } from "@/lib/api";
import { studioHref } from "@/lib/format";
import type { Quote } from "@/lib/types";

const PAGE = 30;
const SOURCE_LABEL: Record<Quote["source"], string> = { seed: "Starter", user: "Yours", ai: "AI" };

export function LibraryView() {
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("all");
  const debounced = useDebounced(search);

  const query = useInfiniteQuery({
    queryKey: ["quotes", debounced, source],
    queryFn: ({ pageParam }) =>
      api.quotes.list({ search: debounced, source: source === "all" ? undefined : source, limit: PAGE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (last) => (last.offset + last.limit < last.total ? last.offset + last.limit : undefined),
  });

  const quotes = query.data?.pages.flatMap((p) => p.items) ?? [];
  const total = query.data?.pages[0]?.total ?? 0;

  return (
    <>
      <PageHeader
        eyebrow="Library"
        title="Every line worth keeping"
        description="Starter quotes, the ones you add, and the AI drafts you chose to save. The library is also the fallback when the AI is off and the list of lines new drafts must not copy."
        actions={<AddQuoteDialog />}
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search text, author or keyword"
            className="h-10 pl-9"
          />
        </div>
        <Tabs value={source} onValueChange={setSource}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="ai">AI</TabsTrigger>
            <TabsTrigger value="user">Yours</TabsTrigger>
            <TabsTrigger value="seed">Starter</TabsTrigger>
          </TabsList>
        </Tabs>
        <span className="text-sm text-muted-foreground sm:w-24 sm:text-right">{total} quotes</span>
      </div>

      {query.isPending ? (
        <div className="columns-1 gap-4 sm:columns-2 lg:columns-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <Skeleton key={i} className="mb-4 rounded-2xl" style={{ height: 120 + (i % 3) * 40 }} />
          ))}
        </div>
      ) : query.isError ? (
        <EmptyState icon={BookOpen} title="Couldn't load the library" description={query.error.message} />
      ) : quotes.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title={debounced ? "Nothing matches that search" : "No quotes here yet"}
          description="Generate some with the AI pipeline, or add your own."
          action={
            <Button asChild variant="outline">
              <Link href="/generate">Generate quotes</Link>
            </Button>
          }
        />
      ) : (
        <>
          <div className="columns-1 gap-4 sm:columns-2 lg:columns-3">
            {quotes.map((q, i) => (
              <QuoteCard key={q.id} quote={q} index={i % PAGE} />
            ))}
          </div>
          {query.hasNextPage && (
            <div className="mt-6 flex justify-center">
              <Button variant="outline" onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
                {query.isFetchingNextPage && <Loader2 className="animate-spin" />} Load more
              </Button>
            </div>
          )}
        </>
      )}
    </>
  );
}

function QuoteCard({ quote, index }: { quote: Quote; index: number }) {
  const remove = useDeleteQuote();
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index, 12) * 0.03 }}
      className="glass group mb-4 break-inside-avoid rounded-2xl p-5 transition hover:border-white/15"
    >
      <p className="font-serif text-lg leading-snug italic">{quote.text}</p>
      {quote.author && <p className="mt-2 text-sm text-gold">— {quote.author}</p>}
      <div className="mt-4 flex flex-wrap items-center gap-1.5">
        <Badge variant={quote.source === "ai" ? "default" : "secondary"} className={quote.source === "ai" ? "bg-violet/20 text-violet" : ""}>
          {SOURCE_LABEL[quote.source]}
        </Badge>
        {quote.quality_score != null && <Badge className="bg-gold/15 font-mono text-gold">★ {quote.quality_score.toFixed(1)}</Badge>}
        {quote.keywords.slice(0, 3).map((k) => (
          <Badge key={k} variant="outline" className="text-muted-foreground">
            {k}
          </Badge>
        ))}
      </div>
      <div className="mt-4 flex gap-1 opacity-100 transition sm:opacity-0 sm:group-hover:opacity-100 sm:focus-within:opacity-100">
        <Button size="sm" variant="ghost" asChild>
          <Link href={studioHref(quote)}>
            <Palette /> Studio
          </Link>
        </Button>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button size="sm" variant="ghost" className="text-muted-foreground hover:text-destructive">
              <Trash2 /> Delete
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete this quote?</AlertDialogTitle>
              <AlertDialogDescription className="font-serif italic">&ldquo;{quote.text}&rdquo;</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Keep it</AlertDialogCancel>
              <AlertDialogAction variant="destructive" onClick={() => remove.mutate(quote.id)}>
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </motion.div>
  );
}
