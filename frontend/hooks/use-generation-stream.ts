"use client";

import { useCallback, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { streamGeneration } from "@/lib/api";
import type {
  CandidateEvent,
  GenerationRequest,
  GenerationResponse,
  RunStartedEvent,
  StepEvent,
} from "@/lib/types";

export type StreamStatus = "idle" | "running" | "done" | "error";

export interface StreamState {
  status: StreamStatus;
  run: RunStartedEvent | null;
  steps: StepEvent[];
  candidates: CandidateEvent[];
  result: GenerationResponse | null;
  error: string | null;
}

const initial: StreamState = { status: "idle", run: null, steps: [], candidates: [], result: null, error: null };

const stepKey = (s: StepEvent) => `${s.node}:${s.round ?? ""}`;

export function useGenerationStream() {
  const [state, setState] = useState<StreamState>(initial);
  const abortRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();

  const start = useCallback(
    async (req: GenerationRequest) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setState({ ...initial, status: "running" });

      try {
        await streamGeneration(
          req,
          (e) => {
            setState((s) => {
              switch (e.event) {
                case "run":
                  return { ...s, run: e.data };
                case "step": {
                  const key = stepKey(e.data);
                  const exists = s.steps.some((x) => stepKey(x) === key);
                  return {
                    ...s,
                    steps: exists ? s.steps.map((x) => (stepKey(x) === key ? e.data : x)) : [...s.steps, e.data],
                  };
                }
                case "candidate":
                  return { ...s, candidates: [...s.candidates, e.data] };
                case "result":
                  return { ...s, result: e.data, status: "done" };
                case "error":
                  return { ...s, error: e.data.message, status: "error" };
              }
            });
          },
          controller.signal,
        );
        setState((s) => (s.status === "running" ? { ...s, status: s.result ? "done" : "error", error: s.error ?? (s.result ? null : "The stream ended early.") } : s));
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          setState((s) => ({ ...s, status: "idle" }));
          return;
        }
        setState((s) => ({ ...s, status: "error", error: (err as Error).message }));
      } finally {
        queryClient.invalidateQueries({ queryKey: ["runs"] });
        queryClient.invalidateQueries({ queryKey: ["system"] });
      }
    },
    [queryClient],
  );

  const cancel = useCallback(() => abortRef.current?.abort(), []);
  const reset = useCallback(() => setState(initial), []);

  return { ...state, start, cancel, reset };
}
