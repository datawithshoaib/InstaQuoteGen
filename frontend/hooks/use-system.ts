"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const systemKey = ["system"] as const;

export function useSystem() {
  return useQuery({ queryKey: systemKey, queryFn: api.system, staleTime: 30_000 });
}
