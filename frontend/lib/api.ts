import type {
  Background,
  GenerationEvent,
  GenerationRequest,
  GenerationResponse,
  Page,
  Post,
  PostQuote,
  PostStyle,
  Quote,
  QuoteCreate,
  RunDetail,
  RunStats,
  RunSummary,
  SystemInfo,
  AspectRatio,
} from "@/lib/types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const API = `${API_URL}/api/v1`;

/** Turn a backend-relative path like /media/posts/x.png into an absolute URL. */
export const mediaUrl = (path: string) => (path.startsWith("http") ? path : `${API_URL}${path}`);

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code: string = "error",
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("Can't reach the API. Is the backend running on " + API_URL + "?", 0, "network");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(body?.error?.message ?? `Request failed (${res.status})`, res.status, body?.error?.code);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

const qs = (params: Record<string, string | number | undefined | null>) => {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") search.set(k, String(v));
  const s = search.toString();
  return s ? `?${s}` : "";
};

export const api = {
  system: () => request<SystemInfo>("/system"),

  quotes: {
    list: (p: { search?: string; source?: string; limit?: number; offset?: number } = {}) =>
      request<Page<Quote>>(`/quotes${qs(p)}`),
    create: (q: QuoteCreate) => post<Quote>("/quotes", q),
    remove: (id: number) => request<void>(`/quotes/${id}`, { method: "DELETE" }),
    random: () => request<Quote>("/quotes/random"),
  },

  generate: (req: GenerationRequest) => post<GenerationResponse>("/generations", req),

  runs: {
    list: (p: { limit?: number; offset?: number } = {}) => request<Page<RunSummary>>(`/runs${qs(p)}`),
    get: (id: string) => request<RunDetail>(`/runs/${id}`),
    stats: () => request<RunStats>("/runs/stats"),
  },

  backgrounds: {
    create: (b: { aspect_ratio: AspectRatio; keywords?: string[]; source?: "auto" | "photo" | "gradient"; palette?: string | null }) =>
      post<Background>("/backgrounds", b),
  },

  posts: {
    list: (p: { limit?: number; offset?: number } = {}) => request<Page<Post>>(`/posts${qs(p)}`),
    create: (body: { quote: PostQuote; style?: Partial<PostStyle>; background_id?: string | null }) =>
      post<Post>("/posts", body),
    remove: (id: string) => request<void>(`/posts/${id}`, { method: "DELETE" }),
  },
};

/**
 * Run the generation pipeline over Server-Sent Events.
 * EventSource only supports GET, so we read the POST response stream ourselves.
 */
export async function streamGeneration(
  req: GenerationRequest,
  onEvent: (e: GenerationEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API}/generations/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(req),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError("Can't reach the API. Is the backend running on " + API_URL + "?", 0, "network");
  }
  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => null);
    throw new ApiError(body?.error?.message ?? `Request failed (${res.status})`, res.status, body?.error?.code);
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replace(/\r\n/g, "\n");
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      let event = "message";
      const data: string[] = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
      }
      if (data.length) onEvent({ event, data: JSON.parse(data.join("\n")) } as GenerationEvent);
    }
  }
}
