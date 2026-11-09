/* eslint-disable @next/next/no-img-element -- rendered posts are served by the API */
"use client";

import { useState } from "react";
import Link from "next/link";
import { useInfiniteQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Images, Loader2, Palette, Sparkles } from "lucide-react";
import { PostDialog } from "@/components/post/post-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeletePost } from "@/hooks/use-mutations";
import { api, mediaUrl } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import type { Post } from "@/lib/types";

const PAGE = 24;

export function GalleryView() {
  const [open, setOpen] = useState<Post | null>(null);
  const remove = useDeletePost();

  const query = useInfiniteQuery({
    queryKey: ["posts"],
    queryFn: ({ pageParam }) => api.posts.list({ limit: PAGE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (last) => (last.offset + last.limit < last.total ? last.offset + last.limit : undefined),
  });
  const posts = query.data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Gallery"
        title="Your finished posts"
        description="Every export lands here with its caption, ready to copy and download."
        actions={
          <Button asChild variant="outline">
            <Link href="/studio">
              <Palette /> New in studio
            </Link>
          </Button>
        }
      />

      {query.isPending ? (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[4/5] rounded-xl" />
          ))}
        </div>
      ) : query.isError ? (
        <EmptyState icon={Images} title="Couldn't load the gallery" description={query.error.message} />
      ) : posts.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No posts yet"
          description="Generate a quote and hit “Make post”, or design one by hand in the studio."
          action={
            <Button asChild>
              <Link href="/generate">Start generating</Link>
            </Button>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-2 items-start gap-4 md:grid-cols-3 xl:grid-cols-4">
            {posts.map((p, i) => (
              <motion.button
                key={p.id}
                type="button"
                onClick={() => setOpen(p)}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: Math.min(i % PAGE, 12) * 0.04 }}
                className="group relative block w-full overflow-hidden rounded-xl ring-1 ring-white/10 transition hover:ring-gold/50"
              >
                <img
                  src={mediaUrl(p.url)}
                  alt={p.quote_text}
                  loading="lazy"
                  className="w-full transition duration-500 group-hover:scale-[1.03]"
                  style={{ aspectRatio: `${p.width} / ${p.height}` }}
                />
                <div className="absolute inset-x-0 bottom-0 translate-y-2 bg-gradient-to-t from-black/85 to-transparent p-3 text-left opacity-0 transition group-hover:translate-y-0 group-hover:opacity-100">
                  <p className="line-clamp-2 font-serif text-sm italic">{p.quote_text}</p>
                  <p className="mt-1 text-[11px] text-white/60">
                    {p.aspect_ratio} · {timeAgo(p.created_at)}
                  </p>
                </div>
              </motion.button>
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

      <PostDialog
        post={open}
        open={!!open}
        onOpenChange={(o) => !o && setOpen(null)}
        onDelete={(p) => remove.mutate(p.id, { onSuccess: () => setOpen(null) })}
      />
    </>
  );
}
