/* eslint-disable @next/next/no-img-element -- rendered posts are served by the API */
"use client";

import { Download, ExternalLink, Trash2 } from "lucide-react";
import { CopyButton } from "@/components/shared/copy-button";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { mediaUrl } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import type { Post } from "@/lib/types";

export function PostDialog({
  post,
  open,
  onOpenChange,
  onDelete,
}: {
  post: Post | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDelete?: (post: Post) => void;
}) {
  return (
    <Dialog open={open && !!post} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92dvh] gap-0 overflow-y-auto p-0 sm:max-w-4xl">
        {post && (
          <div className="grid md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
            <div className="flex items-center justify-center bg-black/60 p-4 md:rounded-l-xl">
              <img
                src={mediaUrl(post.url)}
                alt={post.quote_text}
                className="max-h-[78dvh] w-auto rounded-md shadow-2xl"
              />
            </div>
            <div className="flex flex-col gap-4 p-5">
              <div>
                <DialogTitle className="font-serif text-xl italic">Ready to post</DialogTitle>
                <DialogDescription className="mt-1">
                  {post.width}×{post.height} · {post.aspect_ratio} · {timeAgo(post.created_at)}
                </DialogDescription>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">Caption</p>
                  <CopyButton value={post.caption} label="Copy caption" />
                </div>
                <pre className="max-h-72 overflow-y-auto rounded-lg border border-border bg-black/30 p-3 font-sans text-sm leading-relaxed whitespace-pre-wrap">
                  {post.caption}
                </pre>
              </div>

              {post.photographer_name && (
                <p className="text-xs text-muted-foreground">
                  Photo by{" "}
                  <a
                    href={post.photographer_url ?? "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-foreground underline-offset-2 hover:underline"
                  >
                    {post.photographer_name} <ExternalLink className="size-3" />
                  </a>{" "}
                  on Unsplash
                </p>
              )}

              <div className="mt-auto flex flex-wrap gap-2 pt-2">
                <Button asChild className="flex-1">
                  <a href={mediaUrl(post.download_url)} download>
                    <Download /> Download PNG
                  </a>
                </Button>
                {onDelete && (
                  <Button variant="destructive" onClick={() => onDelete(post)}>
                    <Trash2 /> Delete
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
