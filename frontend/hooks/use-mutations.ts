"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { PostQuote, PostStyle, QuoteCreate } from "@/lib/types";

export function useSaveQuote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (q: QuoteCreate) => api.quotes.create(q),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["quotes"] });
      qc.invalidateQueries({ queryKey: ["system"] });
      toast.success("Saved to your library");
    },
    onError: (err) => toast.error(err.message),
  });
}

export function useDeleteQuote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.quotes.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["quotes"] });
      qc.invalidateQueries({ queryKey: ["system"] });
      toast.success("Quote deleted");
    },
    onError: (err) => toast.error(err.message),
  });
}

export function useCreatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { quote: PostQuote; style?: Partial<PostStyle>; background_id?: string | null }) =>
      api.posts.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["posts"] });
      qc.invalidateQueries({ queryKey: ["system"] });
    },
    onError: (err) => toast.error(err.message),
  });
}

export function useDeletePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.posts.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["posts"] });
      qc.invalidateQueries({ queryKey: ["system"] });
      toast.success("Post deleted");
    },
    onError: (err) => toast.error(err.message),
  });
}
